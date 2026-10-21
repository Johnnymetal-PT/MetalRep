Dim _myJSONerro As String = ""
Try
  ' Envolver o XML recebido
  mstamp = "<root>" & mstamp & "</root>"
  ' Transformar em XMLReader
  Dim stream As New System.IO.MemoryStream(Encoding.UTF8.GetBytes(mstamp))
  Dim reader As System.Xml.XmlReader = New System.Xml.XmlTextReader(stream)
  '---------------------------
  ' Variáveis de Cabeçalho
  '---------------------------
  Dim docType As Integer = 0
  Dim clNo As Integer = 0
  Dim matricula As String = ""
  Dim cdataCarga As Date? = Nothing
  Dim choraCarga As String = "" 'HH:MM
  Dim dMorada As String = ""
  Dim dLocal As String = ""
  Dim dCodPost As String = ""
  Dim paisCod As String = ""   'prefixo/código recebido
  Dim paisNome As String = ""  'nome lido em PAISES
  '---------------------------
  ' Variáveis de Linha (FI/EFI)
  '---------------------------
  Dim ref, design As String
  ref = "" : design = ""
  Dim mqtd As Decimal = 0D
  Dim mTxIVA, mvalor_iva, mvalor_base As Decimal
  Dim mtabiva As Integer = 0
  Dim hasTabIva As Boolean = False
  'Variáveis temporárias da linha recebida no XML
  Dim linhaRef As String = ""
  Dim linhaDesign As String = ""
  Dim linhaQtdTxt As String = ""
  Dim linhaTabIvaTxt As String = ""
  Dim linhaEmCurso As Boolean = False
  Dim column As String = ""
  'Documento
  Dim CreateDocWs As bizlib.ftclass.CreateFTDoc = Nothing
  Dim currentLine As DataRow = Nothing
  Dim newrowWithRefeQtt As DataRow = Nothing
  '-----------------------------------------
  ' Parsing do XML
  '-----------------------------------------
  Do While reader.Read()
    Select Case reader.NodeType
    Case XmlNodeType.Element
      column = reader.Name.ToLowerInvariant()
      'Marcar início de uma linha mesmo que os campos venham vazios.
      'Isto é essencial para aceitar:
      '<ref></ref><design></design><qtd></qtd><tabiva></tabiva>
      If column = "ref" OrElse column = "design" OrElse column = "qtd" OrElse column = "tabiva" Then
        linhaEmCurso = True
      End If
    Case XmlNodeType.Text
      Dim value As String = reader.Value
      Select Case column
        '---------------------------
        ' Cabeçalho - obrigatórios
        '---------------------------
      Case "doctype"
        Integer.TryParse(value.Trim(), docType)
        If docType <= 0 Then
          Return "[{""Erro"":""doctype é obrigatório e deve ser > 0.""}]"
        End If
        'Valida doctype (tipodoc=4)
        Dim dt_td As DataTable = cdata.getdatatable("SELECT ndoc FROM td (NOLOCK) WHERE ndoc='" & CStr(docType) & "' AND tipodoc=4")
        If dt_td Is Nothing OrElse dt_td.Rows.Count = 0 Then
          Return "[{""Erro"":""doctype (número interno do documento PHC) não é válido!!""}]"
        End If
        'Criar documento se já tivermos doctype/no
        If CreateDocWs Is Nothing AndAlso docType > 0 AndAlso clNo > 0 Then
          CreateDocWs = New bizlib.ftclass.CreateFTDoc(docType, clNo)
        End If
      Case "no"
        Integer.TryParse(value.Trim(), clNo)
        If clNo <= 0 Then
          Return "[{""Erro"":""no (nº cliente) é obrigatório e deve ser > 0.""}]"
        End If
        'Valida Cliente
        Dim dt_cl As DataTable = cdata.getdatatable("SELECT no FROM cl (NOLOCK) WHERE cl.no='" & CStr(clNo) & "' AND cl.estab=0")
        If dt_cl Is Nothing OrElse dt_cl.Rows.Count = 0 Then
          Return "[{""Erro"":""Cliente nº " & clNo & " não existe no PHC!""}]"
        End If
        'Criar documento se já tivermos doctype/no
        If CreateDocWs Is Nothing AndAlso docType > 0 AndAlso clNo > 0 Then
          CreateDocWs = New bizlib.ftclass.CreateFTDoc(docType, clNo)
        End If
      Case "matricula"
        matricula = value.Trim()
      Case "cdata"
        Dim tmpDate As DateTime
        If DateTime.TryParse(value.Trim(), tmpDate) Then
          cdataCarga = tmpDate.Date
        Else
          Return "[{""Erro"":""cdata inválida (obrigatório). Use YYYY-MM-DD.""}]"
        End If
      Case "chora"
        Dim tmpTime As DateTime
        If DateTime.TryParseExact(value.Trim(), "HH:mm", Global.System.Globalization.CultureInfo.InvariantCulture,
            Global.System.Globalization.DateTimeStyles.None, tmpTime) Then
          choraCarga = tmpTime.ToString("HHmm")
        Else
          Return "[{""Erro"":""chora inválida (obrigatório). Use HH:MM.""}]"
        End If
      Case "dmorada"
        dMorada = value.Trim()
      Case "dlocal"
        dLocal = value.Trim()
      Case "dcodpost"
        dCodPost = value.Trim()
      Case "pais"
        paisCod = value.Trim()
        '---------------------------
        ' Linhas (FI/EFI)
        '---------------------------
      Case "ref"
        linhaRef = value.Trim()
      Case "design"
        linhaDesign = value.Trim()
      Case "qtd"
        linhaQtdTxt = value.Trim()
      Case "tabiva"
        linhaTabIvaTxt = value.Trim()
      End Select
    Case XmlNodeType.EndElement
      Dim endColumn As String = reader.Name.ToLowerInvariant()
      'Fechar a linha quando termina o tabiva.
      'Funciona mesmo quando <tabiva></tabiva> vem vazio,
      'porque EndElement existe sempre.
      If endColumn = "tabiva" AndAlso linhaEmCurso Then
        If CreateDocWs Is Nothing Then
          If docType > 0 AndAlso clNo > 0 Then
            CreateDocWs = New bizlib.ftclass.CreateFTDoc(docType, clNo)
          Else
            Return "[{""Erro"":""Não foi possível criar linhas porque o documento ainda não foi criado.""}]"
          End If
        End If
        'Criar sempre uma nova linha.
        'Permite linha normal, linha só descrição e linha totalmente em branco.
        newrowWithRefeQtt = CreateDocWs.Addnewline()
        'Referência
        If linhaRef <> "" Then
          newrowWithRefeQtt.Item("ref") = linhaRef
          'Obrigatório executar actLinha sempre que a linha tenha referência.
          'Isto faz o PHC carregar os dados da referência/artigo.
          CreateDocWs.actLinha(newrowWithRefeQtt)
        End If
        'Descrição
        If linhaDesign <> "" Then
          newrowWithRefeQtt.Item("design") = linhaDesign
        End If
        'Quantidade: só preenche se vier valor.
        'Linhas em branco ou só descrição não forçam qtt = 0.
        'Quantidade: só preenche se vier valor.
        'Na API, o separador decimal esperado é ponto:
        '1.000 = 1 unidade
        '2.500 = 2,5 unidades
        If linhaQtdTxt <> "" Then
          Dim qtdTxtNormalizado As String = linhaQtdTxt.Trim()
          If Decimal.TryParse(qtdTxtNormalizado,
              Global.System.Globalization.NumberStyles.Any,
              Global.System.Globalization.CultureInfo.InvariantCulture,
              mqtd) Then
            newrowWithRefeQtt.Item("qtt") = mqtd
          Else
            Return "[{""Erro"":""Quantidade inválida na linha: " & linhaQtdTxt.Replace("""", "'") & """}]"
          End If
        End If
        'Tabiva: só preenche e valida se vier valor.
        'Se vier vazio, não vai à tabela TAXASIVA.
        If linhaTabIvaTxt <> "" Then
          If Integer.TryParse(linhaTabIvaTxt, mtabiva) Then
            newrowWithRefeQtt.Item("tabiva") = mtabiva
            Dim dt_txIva As DataTable =
            cdata.getdatatable("SELECT TAXA FROM TAXASIVA (NOLOCK) WHERE CODIGO = '" & mtabiva & "'")
            If dt_txIva IsNot Nothing AndAlso dt_txIva.Rows.Count > 0 Then
              mTxIVA = Convert.ToDecimal(dt_txIva.Rows(0)("TAXA"))
              newrowWithRefeQtt.Item("iva") = mTxIVA
            Else
              _myJSONerro = "["
              _myJSONerro += "{""Erro"":""Não foi possível obter a taxa de IVA (sem registos em TAXASIVA para o código " & CStr(mtabiva) & ") ou tabela IVA inválida.""}"
              _myJSONerro += "]"
              Return _myJSONerro
            End If
          Else
            Return "[{""Erro"":""Tabela de IVA inválida na linha: " & linhaTabIvaTxt.Replace("""", "'") & """}]"
          End If
        End If
        'Limpar variáveis temporárias para a próxima linha
        linhaRef = ""
        linhaDesign = ""
        linhaQtdTxt = ""
        linhaTabIvaTxt = ""
        linhaEmCurso = False
      End If
    End Select
  Loop
  '---------------------------------------------------
  ' Valida obrigatórios do cabeçalho (após parsing)
  '---------------------------------------------------
  If docType <= 0 Then
    Return "[{""Erro"":""doctype é obrigatório e deve ser > 0.""}]"
  End If
  If clNo <= 0 Then
    Return "[{""Erro"":""no (nº cliente) é obrigatório e deve ser > 0.""}]"
  End If
  If CreateDocWs Is Nothing Then
    CreateDocWs = New bizlib.ftclass.CreateFTDoc(docType, clNo)
  End If
  If matricula.Trim() = "" Then
    Return "[{""Erro"":""matricula é obrigatória.""}]"
  End If
  If matricula.Length > 12 Then
    Return "[{""Erro"":""matricula excede 12 caracteres.""}]"
  End If
  If Not cdataCarga.HasValue Then
    Return "[{""Erro"":""data de carga (cdata) é obrigatória.""}]"
  End If
  If choraCarga.Trim() = "" Then
    Return "[{""Erro"":""hora de carga (chora) é obrigatória (HH:MM).""}]"
  End If
  If dMorada.Trim() = "" Then
    Return "[{""Erro"":""morada de descarga é obrigatória.""}]"
  End If
  If dMorada.Length > 55 Then
    Return "[{""Erro"":""morada de descarga excede 55 caracteres.""}]"
  End If
  If dLocal.Trim() = "" Then
    Return "[{""Erro"":""localidade de descarga é obrigatória.""}]"
  End If
  If dLocal.Length > 43 Then
    Return "[{""Erro"":""localidade de descarga excede 43 caracteres.""}]"
  End If
  If dCodPost.Trim() = "" Then
    Return "[{""Erro"":""código postal de descarga é obrigatório.""}]"
  End If
  If dCodPost.Length > 45 Then
    Return "[{""Erro"":""código postal de descarga excede 45 caracteres.""}]"
  End If
  If paisCod.Trim() = "" Then
    Return "[{""Erro"":""país de descarga é obrigatório (código/prefixo).""}]"
  End If
  'Lookup país
  Dim codEsc As String = paisCod.Replace("'", "''")
  Dim dtPais As DataTable =
  cdata.getdatatable("SELECT TOP 1 NOME FROM PAISES (NOLOCK) WHERE NOMEABRV = '" & codEsc & "'")
  If dtPais Is Nothing OrElse dtPais.Rows.Count = 0 Then
    Return "[{""Erro"":""País inválido: não existe na tabela de Países para o prefixo=" & paisCod & ".""}]"
  End If
  paisNome = CStr(dtPais.Rows(0)("NOME")).Trim()
  If paisNome = "" Then
    Return "[{""Erro"":""País inválido: NOME vazio em PAISES para CODNUM=" & paisCod & ".""}]"
  End If
  If paisNome.Length > 55 Then
    paisNome = paisNome.Substring(0, 55)
  End If
  '---------------------------------------------------
  ' Preenchimento dos dados de transporte
  '---------------------------------------------------
  CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("cdata") = cdataCarga.Value
  CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("chora") = choraCarga  'HHMM conforme pedido
  CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("matricula") = matricula
  CreateDocWs.MainformDataset.Tables("EFT3").Rows(0).Item("u_dmorada") = dMorada
  CreateDocWs.MainformDataset.Tables("EFT3").Rows(0).Item("u_dlocal") = dLocal
  CreateDocWs.MainformDataset.Tables("EFT3").Rows(0).Item("u_dcodpost") = dCodPost
  CreateDocWs.MainformDataset.Tables("EFT3").Rows(0).Item("u_dpais") = paisNome
  '---------------------------------------------------
  ' Validação do motivo de isenção
  '---------------------------------------------------
  Dim mcodMot As String = ""
  'Tenta em EFT2 primeiro, com fallback para EFT
  If CreateDocWs.MainformDataset.Tables.Contains("EFT2") AndAlso
    CreateDocWs.MainformDataset.Tables("EFT2").Rows.Count > 0 AndAlso
    Not IsDBNull(CreateDocWs.MainformDataset.Tables("EFT2").Rows(0)("codmotiseimp")) Then
    mcodMot = Trim(CStr(CreateDocWs.MainformDataset.Tables("EFT2").Rows(0)("codmotiseimp")))
  ElseIf CreateDocWs.MainformDataset.Tables.Contains("EFT") AndAlso
    CreateDocWs.MainformDataset.Tables("EFT").Rows.Count > 0 AndAlso
    Not IsDBNull(CreateDocWs.MainformDataset.Tables("EFT").Rows(0)("codmotiseimp")) Then
    mcodMot = Trim(CStr(CreateDocWs.MainformDataset.Tables("EFT").Rows(0)("codmotiseimp")))
  End If
  If CreateDocWs.MainformDataset.Tables.Contains("EFI") Then
    For Each dr As DataRow In CreateDocWs.MainformDataset.Tables("EFI").Rows
      Dim ivaVal As Decimal = 0D
      If Not IsDBNull(dr("IVA")) AndAlso Trim(CStr(dr("IVA"))) <> "" Then
        Decimal.TryParse(CStr(dr("IVA")), ivaVal)
      End If
      If ivaVal = 0D AndAlso mcodMot = "" Then
        Return "[{""Erro"":""O motivo de isenção de imposto é obrigatório (codmotiseimp no cabeçalho / cliente).""}]"
      End If
    Next
  End If
  '---------------------------------------------------
  ' Gravação do documento
  '---------------------------------------------------
  Dim nvftstamp As String = CreateDocWs.MainformDataset.Tables("EFT").Rows(0).Item("eftstamp")
  CreateDocWs.ActTotais()
  Try
    CreateDocWs.Save()
    Dim nrft As Integer = cdata.getumvalorinteger("SELECT fno FROM ft WHERE ftstamp = '" & nvftstamp.Replace("'", "''") & "'")
    Dim anoft As Integer = cdata.getumvalorinteger("SELECT ftano FROM ft (NOLOCK) WHERE ftstamp = '" & nvftstamp.Replace("'", "''") & "'")
    'Diretoria do PDF
    Dim diretoria As String = HttpContext.Current.Server.MapPath("~").Trim() & "\pimages\anexos\guiastransporte\"
    Dim nomeFicheiro As String = "GT" & CStr(docType) & "_" & anoft.ToString() & "_" & nrft.ToString() & ".pdf"
    Dim report As New FTreport(nvftstamp, 11)
    report.wrstamp = "314be2a0a6ee9e4c58c6c1" 'confirma se isto é fixo no teu ambiente
    With report.GetReportResultFromCache
    If .FilesResult.Any Then
      'Guardar os Bytes do Relatório
      Dim pdf = .FilesResult(0).FileContents
      Dim oFileStream1 As System.IO.FileStream
      oFileStream1 = New System.IO.FileStream(diretoria & nomeFicheiro, System.IO.FileMode.Create)
      oFileStream1.Write(pdf, 0, pdf.Length)
      oFileStream1.Close()
    End If
  End With
Dim linkft As String = "http://192.168.5.4/Intranet_Triplex/pimages/anexos/guiastransporte/" & nomeFicheiro
Dim _myJSON As String = "[{""Ano"":""" & anoft.ToString() & """,""GTNum"":""" & nrft.ToString() & """,""PDF"":""" & linkft & """}]"
Return _myJSON
Catch exSave As Exception
Return "[{""Erro"":""Ocorreu um erro ao criar o documento: " & exSave.Message.Replace("""", "'") & """}]"
End Try
Catch ex As Exception
Return "[{""Erro"":""Falha geral: " & ex.Message.Replace("""", "'") & """}]"
End Try