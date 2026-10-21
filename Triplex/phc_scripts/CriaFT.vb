mstamp = "<root>" & mstamp & "</root>"
' Transformação da string recebida pelo webservice em XML
Dim stream As New System.IO.MemoryStream(Encoding.UTF8.GetBytes(mstamp))
Dim reader As System.Xml.XmlReader = New System.Xml.XmlTextReader(stream)
Dim invCulture As System.Globalization.CultureInfo = System.Globalization.CultureInfo.InvariantCulture
Dim numStyle As System.Globalization.NumberStyles = System.Globalization.NumberStyles.Any
' Criação das variáveis, doctype é nº interno do documento, clno é nº do cliente
Dim docType, clNo As Integer
Dim mprunit, mqtd As Decimal
Dim mccusto As String = ""
Dim fno As String = ""
Dim ftstamp As String = ""
Dim formapag As String = ""
Dim mADano1, mADano2, mADano3, mADano4, mADano5 As Integer
Dim mADano6, mADano7, mADano8, mADano9, mADano10 As Integer
Dim mADnum1, mADnum2, mADnum3, mADnum4, mADnum5 As Integer
Dim mADnum6, mADnum7, mADnum8, mADnum9, mADnum10 As Integer
Dim column As String = ""
Dim ref, design As String
ref = ""
design = ""
Dim mtabiva As Integer
Dim mTxIVA, mvalor_iva, mvalor_base As Decimal
Dim mDesconto1, mDesconto2, mDesconto3 As Decimal
Dim _myJSONerro As String
Dim CreateDocWs As bizlib.ftclass.CreateFTDoc
Dim newrowWithRefeQtt As DataRow = Nothing
Do While reader.Read()
    Select Case reader.NodeType
        Case System.Xml.XmlNodeType.Element
            column = reader.Name.ToLower().Trim()
            ' Cada <ref> marca o início de uma nova linha, mesmo que a referência venha vazia.
            If column = "ref" AndAlso CreateDocWs IsNot Nothing Then
                newrowWithRefeQtt = CreateDocWs.Addnewline()
                ' Inicialização defensiva para evitar valores herdados ou nulos problemáticos.
                newrowWithRefeQtt.Item("ref") = ""
                newrowWithRefeQtt.Item("design") = ""
                newrowWithRefeQtt.Item("qtt") = 0D
                newrowWithRefeQtt.Item("epv") = 0D
                newrowWithRefeQtt.Item("desconto") = 0D
                newrowWithRefeQtt.Item("desc2") = 0D
                newrowWithRefeQtt.Item("desc3") = 0D
                CreateDocWs.actLinha(newrowWithRefeQtt)
            End If
        Case System.Xml.XmlNodeType.Text
            Dim value As String = reader.Value
            If value Is Nothing Then
                value = ""
            End If
            value = value.Trim()
            Select Case column
                Case "doctype", "no"
                    If column = "no" Then
                        Integer.TryParse(value, clNo)
                        ' Valida se cliente existe
                        Dim dt_cl As DataTable = cdata.getdatatable(
                            "select no from cl (nolock) where cl.no='" + CStr(clNo) + "' and cl.estab=0"
                        )
                        If Not dt_cl.HaveRows Then
                            _myJSONerro = "["
                            _myJSONerro += "{""Erro"":""Cliente nº " + CStr(clNo) + " não existe no PHC!""}"
                            _myJSONerro += "]"
                            Return _myJSONerro
                        End If
                    ElseIf column = "doctype" Then
                        Integer.TryParse(value, docType)
                        ' Valida se tipo documento fatura
                        Dim dt_td As DataTable = cdata.getdatatable(
                            "select ndoc from td (nolock) where ndoc='" + CStr(docType) + "' and tipodoc=1"
                        )
                        If Not dt_td.HaveRows Then
                            _myJSONerro = "["
                            _myJSONerro += "{""Erro"":""doctype (número interno do documento PHC) não é válido!!""}"
                            _myJSONerro += "]"
                            Return _myJSONerro
                        End If
                    End If
                    If docType > 0 AndAlso clNo > 0 AndAlso CreateDocWs Is Nothing Then
                        Try
                            ' Cria o documento de faturação
                            CreateDocWs = New bizlib.ftclass.CreateFTDoc(docType, clNo)
                            ' Preencher o campo: Data
                            CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("cdata") = Date.Now.Date
                            ' Preencher o campo: Hora
                            CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("chora") = DateTime.Now.ToString("HHmm")
                            ' Preencher o campo: linha final
                            CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("final") = "Documento criado programaticamente via API"
                        Catch ex As System.Exception
                            ex.AddError("Tipo de documento ou o nº cliente são obrigatórios.")
                            Exit Do
                        End Try
                    End If
                Case "formapag"
                    formapag = value
                    ' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "formapaf", formapag, false)
                    '
                    ' If Len(formapag) > 0 Then
                    '     Dim mcformapag As String = cdata.getumvalorstring($"select campo from dytable (nolock) where entityname='a_tptit' and campo = '{formapag}'")
                    '
                    '     If Len(mcformapag) > 0 Then
                    '         CreateDocWs.MainformDataset.Tables(0).Rows(0).Item("TPTIT") = formapag
                    '     Else
                    '         Return "Forma de pagamento inválida ou não existente"
                    '     End If
                    ' End If
                Case "adano1", "adnum1"
                    If column = "adano1" Then
                        Integer.TryParse(value, mADano1)
                    Else
                        Integer.TryParse(value, mADnum1)
                    End If
                Case "adano2", "adnum2"
                    If column = "adano2" Then
                        Integer.TryParse(value, mADano2)
                    Else
                        Integer.TryParse(value, mADnum2)
                    End If
                Case "adano3", "adnum3"
                    If column = "adano3" Then
                        Integer.TryParse(value, mADano3)
                    Else
                        Integer.TryParse(value, mADnum3)
                    End If
                Case "adano4", "adnum4"
                    If column = "adano4" Then
                        Integer.TryParse(value, mADano4)
                    Else
                        Integer.TryParse(value, mADnum4)
                    End If
                Case "adano5", "adnum5"
                    If column = "adano5" Then
                        Integer.TryParse(value, mADano5)
                    Else
                        Integer.TryParse(value, mADnum5)
                    End If
                Case "adano6", "adnum6"
                    If column = "adano6" Then
                        Integer.TryParse(value, mADano6)
                    Else
                        Integer.TryParse(value, mADnum6)
                    End If
                Case "adano7", "adnum7"
                    If column = "adano7" Then
                        Integer.TryParse(value, mADano7)
                    Else
                        Integer.TryParse(value, mADnum7)
                    End If
                Case "adano8", "adnum8"
                    If column = "adano8" Then
                        Integer.TryParse(value, mADano8)
                    Else
                        Integer.TryParse(value, mADnum8)
                    End If
                Case "adano9", "adnum9"
                    If column = "adano9" Then
                        Integer.TryParse(value, mADano9)
                    Else
                        Integer.TryParse(value, mADnum9)
                    End If
                Case "adano10", "adnum10"
                    If column = "adano10" Then
                        Integer.TryParse(value, mADano10)
                    Else
                        Integer.TryParse(value, mADnum10)
                    End If
                Case "ref"
                    If CreateDocWs Is Nothing Then
                        Sistema.adderror("Script do Utilizador", "Não foi possível adicionar a referência pois o documento não foi criado")
                        Exit Select
                    End If
                    If newrowWithRefeQtt Is Nothing Then
                        newrowWithRefeQtt = CreateDocWs.Addnewline()
                        CreateDocWs.actLinha(newrowWithRefeQtt)
                    End If
                    ref = value.Trim()
                    newrowWithRefeQtt.Item("ref") = ref
                Case "design"
                    If CreateDocWs Is Nothing Then
                        Exit Select
                    End If
                    If newrowWithRefeQtt Is Nothing Then
                        newrowWithRefeQtt = CreateDocWs.Addnewline()
                        newrowWithRefeQtt.Item("ref") = ""
                        newrowWithRefeQtt.Item("qtt") = 0D
                        newrowWithRefeQtt.Item("epv") = 0D
                        CreateDocWs.actLinha(newrowWithRefeQtt)
                    End If
                    design = value.Trim()
                    newrowWithRefeQtt.Item("design") = design
                Case "desc1"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Decimal.TryParse(value.Trim(), numStyle, invCulture, mDesconto1) Then
                        Return "[{""Erro"":""Valor inválido no campo desc1: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("desconto") = mDesconto1
                Case "desc2"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Decimal.TryParse(value.Trim(), numStyle, invCulture, mDesconto2) Then
                        Return "[{""Erro"":""Valor inválido no campo desc2: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("desc2") = mDesconto2
                Case "desc3"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Decimal.TryParse(value.Trim(), numStyle, invCulture, mDesconto3) Then
                        Return "[{""Erro"":""Valor inválido no campo desc3: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("desc3") = mDesconto3
                Case "tabiva"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Integer.TryParse(value.Trim(), mtabiva) Then
                        Return "[{""Erro"":""Valor inválido no campo tabiva: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("tabiva") = mtabiva
                    Dim dt_txIva As DataTable = cdata.getdatatable(
                        "SELECT TAXA FROM TAXASIVA (NOLOCK) WHERE CODIGO = '" & mtabiva & "'"
                    )
                    If dt_txIva IsNot Nothing AndAlso dt_txIva.Rows.Count > 0 Then
                        mTxIVA = Convert.ToDecimal(dt_txIva.Rows(0)("TAXA"))
                        newrowWithRefeQtt.Item("iva") = mTxIVA
                    Else
                        _myJSONerro = "["
                        _myJSONerro += "{""Erro"":""Não foi possível obter a taxa de IVA para o código " + CStr(mtabiva) + " ou tabela IVA inválida.""}"
                        _myJSONerro += "]"
                        Return _myJSONerro
                    End If
                Case "qtd"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Decimal.TryParse(value.Trim(), numStyle, invCulture, mqtd) Then
                        Return "[{""Erro"":""Valor inválido no campo qtd: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("qtt") = mqtd
                Case "prunit"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    If Not Decimal.TryParse(value.Trim(), numStyle, invCulture, mprunit) Then
                        Return "[{""Erro"":""Valor inválido no campo prunit: " & value.Replace("""", "'") & """}]"
                    End If
                    newrowWithRefeQtt.Item("epv") = mprunit
                    CreateDocWs.Ftiliq(newrowWithRefeQtt)
                Case "ccusto"
                    If newrowWithRefeQtt Is Nothing Then
                        Exit Select
                    End If
                    If value.Trim() = "" Then
                        Exit Select
                    End If
                    mccusto = value.Trim()
                    If mccusto.Length > 20 Then
                        Return "[{""Mensagem"":""Campo Centro de custo não pode ter mais de 20 carateres""}]"
                    Else
                        Dim dt_cc As DataTable = cdata.getdatatable(
                            "SELECT cct FROM cu (NOLOCK) WHERE cct = '" & mccusto.Replace("'", "''") & "'"
                        )
                        If dt_cc IsNot Nothing AndAlso dt_cc.Rows.Count > 0 Then
                            newrowWithRefeQtt("FICCUSTO") = mccusto
                        Else
                            Return "[{""Mensagem"":""O centro de custo " & mccusto.Replace("""", "'") & " não existe na tabela do PHC.""}]"
                        End If
                    End If
            End Select
    End Select
Loop
' Regra: se existir linha EFI com IVA = 0 ou vazio e no cabeçalho codmotiseimp estiver vazio -> erro
Dim codMot As String = CreateDocWs.MainformDataset.Tables("EFT2").Rows(0).Item("codmotiseimp")
' codmotiseimp no cabeçalho
Dim mcodMot As String = ""
If Not IsDBNull(codMot) Then
    mcodMot = Trim(CStr(codMot))
End If
For Each dr As DataRow In CreateDocWs.MainformDataset.Tables("EFI").Rows
    ' IVA na linha, tratando nulos/vazios
    Dim ivaVal As Decimal = 0D
    If Not IsDBNull(dr("IVA")) AndAlso Trim(CStr(dr("IVA"))) <> "" Then
        Decimal.TryParse(CStr(dr("IVA")), ivaVal)
    End If
    If ivaVal = 0D AndAlso mcodMot = "" Then
        _myJSONerro = "["
        _myJSONerro += "{""Erro"":""O motivo de isenção de imposto obrigatório.Preencher no cliente""}"
        _myJSONerro += "]"
        Return _myJSONerro
        ' CreateDocWs.MainformDataset.Tables(1).Rows(0).Item("motiseimp") = "Isento artigo 14.º do RITI"
        ' CreateDocWs.MainformDataset.Tables(1).Rows(0).Item("codmotiseimp") = "M16"
        Exit For
    End If
Next
' Guarda o stamp do documento
Dim nvftstamp As String = CreateDocWs.MainformDataset.Tables("EFT").Rows(0).Item("eftstamp")
' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "nvftstamp", nvftstamp, false)
If CreateDocWs IsNot Nothing Then
    ' INÍCIO - Regulariza Adiantamentos
    Dim mSelRD As String = ""
    mSelRD = "select rdstamp,etotal evreg,total vreg,0 eivav1,0 ivav1,0 eivav2,0 ivav2,0 eivav3,0 ivav3,0 eivav4,0 ivav4,0 eivav5,0 ivav5,0 eivav6,0 ivav6, "
    mSelRD = mSelRD + "0 eivav7,0 ivav7,0 eivav8,0 ivav8,0 eivav9,0 ivav9,0 vmreg,'' ftrdstamp,anulado,rno,0 evemissao,0 vemissao from rd (nolock) "
    mSelRD = mSelRD + "where no='" + CStr(clNo) + "' and "
    mSelRD = mSelRD + "((rdano='" + CStr(mADano1) + "' and rno='" + CStr(mADnum1) + "') or (rdano='" + CStr(mADano2) + "' and rno='" + CStr(mADnum2) + "') or "
    mSelRD = mSelRD + "(rdano='" + CStr(mADano3) + "' and rno='" + CStr(mADnum3) + "') or (rdano='" + CStr(mADano4) + "' and rno='" + CStr(mADnum4) + "') or "
    mSelRD = mSelRD + "(rdano='" + CStr(mADano5) + "' and rno='" + CStr(mADnum5) + "') or (rdano='" + CStr(mADano6) + "' and rno='" + CStr(mADnum6) + "') or "
    mSelRD = mSelRD + "(rdano='" + CStr(mADano7) + "' and rno='" + CStr(mADnum7) + "') or (rdano='" + CStr(mADano8) + "' and rno='" + CStr(mADnum8) + "') or "
    mSelRD = mSelRD + "(rdano='" + CStr(mADano9) + "' and rno='" + CStr(mADnum9) + "') or (rdano='" + CStr(mADano10) + "' and rno='" + CStr(mADnum10) + "')) "
    ' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "query mSelRD", mSelRD, false)
    Dim dt_rd As DataTable = cdata.getdatatable(mSelRD)
    Dim FtRdTable = CreateDocWs.MainformDataset.Tables("eftrd")
    For Each item In dt_rd.Rows
        ' Validar se o adiantamento está anulado
        If item("anulado") = 0 Then
            ' Para cada linha do RD ir buscar os dados ao CC
            Dim cctable As DataTable = cdata.getdatatable(
                "select cc.ccstamp, cc.rdstamp,cc.cmdesc,cc.nrdoc, cc.fref,cc.moeda,cc.datalc, " +
                "- (cc.edeb - cc.edebf - (cc.ecred - cc.ecredf)) as euremi,ISNULL(rd.etotal,-(cc.edeb - cc.ecred)) as evori,rd.iva,rd.tabiva " +
                "from cc (nolock) inner join rd (nolock) on cc.rdstamp=rd.rdstamp " +
                "where cc.rdstamp='" + item("rdstamp") + "'"
            )
            Dim ccRow As DataRow = cctable.Rows(0)
            If ccRow.ItemToDecimal("euremi") > 0 Then
                Dim iFtRdRowIndex = FtFormClass.NewInstance(CreateDocWs.MainformDataset, CreateDocWs.Td).NewFtRdLine()
                FtRdTable(iFtRdRowIndex).Item("ccstamp") = ccRow.ItemToString("ccstamp")
                FtRdTable(iFtRdRowIndex).Item("rdstamp") = ccRow.ItemToString("rdstamp")
                FtRdTable(iFtRdRowIndex).Item("cdesc") = ccRow.ItemToString("cmdesc")
                FtRdTable(iFtRdRowIndex).Item("nrdoc") = ccRow.ItemToString("nrdoc")
                FtRdTable(iFtRdRowIndex).Item("fref") = ccRow.ItemToString("fref")
                FtRdTable(iFtRdRowIndex).Item("evemissao") = ccRow.ItemToString("euremi")
                FtRdTable(iFtRdRowIndex).Item("vemissao") = EuroToEsc(ccRow.ItemToDecimal("euremi"))
                FtRdTable(iFtRdRowIndex).Item("evreg") = ccRow.ItemToDecimal("euremi")
                FtRdTable(iFtRdRowIndex).Item("vreg") = EuroToEsc(ccRow.ItemToDecimal("euremi"))
                FtRdTable(iFtRdRowIndex).Item("moeda") = ccRow.ItemToString("moeda")
                FtRdTable(iFtRdRowIndex).Item("datalc") = ccRow.ItemToString("datalc")
                If ccRow.ItemToDecimal("iva") > 0D Then
                    If ccRow.ItemToString("tabiva") = "2" Then
                        mvalor_base = Decimal.Round(
                            ccRow.ItemToDecimal("euremi") / (1D + (ccRow.ItemToDecimal("iva") / 100D)),
                            2,
                            MidpointRounding.AwayFromZero
                        )
                        mvalor_iva = Decimal.Round(
                            ccRow.ItemToDecimal("euremi") - mvalor_base,
                            2,
                            MidpointRounding.AwayFromZero
                        )
                        FtRdTable(iFtRdRowIndex).Item("eivav2") = mvalor_iva
                        FtRdTable(iFtRdRowIndex).Item("ivav2") = EuroToEsc(mvalor_iva)
                    End If
                End If
            Else
                _myJSONerro = "["
                _myJSONerro += "{""Erro"":""O adiantamento nº" + ccRow.ItemToString("nrdoc") + " já está regularizado.""}"
                _myJSONerro += "]"
                Return _myJSONerro
            End If
        Else
            _myJSONerro = "["
            _myJSONerro += "{""Erro"":""O adiantamento nº " + item("rno").ToString() + " está anulado.""}"
            _myJSONerro += "]"
            Return _myJSONerro
        End If
    Next
    bizlib.ftclass.FtAddReg.FtRdActTotal(
        CreateDocWs.MainformDataset.Tables("EFT").Rows(0),
        CreateDocWs.MainformDataset.Tables("EFT3").Rows(0),
        FtRdTable
    )
    Dim vardERdtotal As Decimal = CreateDocWs.MainformDataset.Tables("EFT").Rows(0).Item("ERDTOTAL")
    CreateDocWs.ActTotais()
    Dim vardtotalDoc As Decimal = CreateDocWs.MainformDataset.Tables("EFT").Rows(0).Item("etotal")
    If vardERdtotal > vardtotalDoc Then
        _myJSONerro = "["
        _myJSONerro += "{""Erro"":""Desculpe, mas os valores das regularizações de adiantamentos não podem ser superiores ao valor do documento.""}"
        _myJSONerro += "]"
        Return _myJSONerro
    End If
    Try
        CreateDocWs.Save()
        ' Lançar N/C Adiantamento respetiva - INÍCIO
        Dim ioList As New List(Of DataRow)
        Dim tblFTRD As DataTable = CreateDocWs.MainformDataset.Tables("FTRD")
        For Each dr_ftrd As DataRow In tblFTRD.Rows
            ' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "ftrdstamp", dr_ftrd("ftrdstamp"), false)
            Dim item As DataRow = tblFTRD.NewRow()
            item("ftrdstamp") = dr_ftrd("ftrdstamp")
            item("rdstamp") = dr_ftrd("rdstamp")
            item("ftstamp") = dr_ftrd("ftstamp")
            item("ccstamp") = dr_ftrd("ccstamp")
            item("nrdoc") = dr_ftrd("nrdoc")
            item("fref") = dr_ftrd("fref")
            item("evreg") = dr_ftrd("evreg")
            item("vreg") = dr_ftrd("vreg")
            item("evemissao") = dr_ftrd("evemissao")
            item("vemissao") = dr_ftrd("vemissao")
            item("moeda") = dr_ftrd("moeda")
            item("eivav1") = dr_ftrd("eivav1")
            item("ivav1") = dr_ftrd("ivav1")
            item("eivav2") = dr_ftrd("eivav2")
            item("ivav2") = dr_ftrd("ivav2")
            item("eivav3") = dr_ftrd("eivav3")
            item("ivav3") = dr_ftrd("ivav3")
            item("eivav4") = dr_ftrd("eivav4")
            item("ivav4") = dr_ftrd("ivav4")
            item("eivav5") = dr_ftrd("eivav5")
            item("ivav5") = dr_ftrd("ivav5")
            item("eivav6") = dr_ftrd("eivav6")
            item("ivav6") = dr_ftrd("ivav6")
            item("eivav7") = dr_ftrd("eivav7")
            item("ivav7") = dr_ftrd("ivav7")
            item("eivav8") = dr_ftrd("eivav8")
            item("ivav8") = dr_ftrd("ivav8")
            item("eivav9") = dr_ftrd("eivav9")
            item("ivav9") = dr_ftrd("ivav9")
            item("vmemissao") = dr_ftrd("vmemissao")
            item("vmreg") = dr_ftrd("vmreg")
            item("ecambio") = dr_ftrd("ecambio")
            item("edifcambio") = dr_ftrd("edifcambio")
            item("difcambio") = dr_ftrd("difcambio")
            ioList.Add(item)
        Next
        '''------------------------- debug ioList
        ' Dim sb As New System.Text.StringBuilder()
        '
        ' For Each r As DataRow In ioList
        '     For Each c As DataColumn In r.Table.Columns
        '         sb.AppendLine($"{c.ColumnName}: {If(IsDBNull(r(c)), "", CStr(r(c)))}")
        '     Next
        '
        '     sb.AppendLine("--------------------------------------------------")
        ' Next
        '
        ' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "ioList (dump completo)", sb.ToString(), False)
        '''-------------------------------------- end debug
        If CreateDocWs.MainformDataset.Tables("FTRD").Rows.Count > 0 Then
            bizlib.ftclass.FtAddReg.CreateFtRdNewDoc(ioList, CreateDocWs.MainformDataset)
        End If
        ' FIM - Lançar N/C Adiantamento respetiva
        ' FIM - Regulariza Adiantamentos
        ' Integra contabilidade - Início
        Dim ll_Integra As String = cdata.getumvalorstring("AUTOML", "TD", "ndoc='" + CStr(docType) + "'")
        If ll_Integra = True Then
            Dim tdrow = WebControlLib.TdRow.GetNewTdRow(docType)
            ' xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt", "nvftstamp vou integrar", nvftstamp)
            ' Mlft.IntegrarOnlineTask(tdrow, $"'{nvftstamp}'", "Descrição", False, "", 0, False, True)
            Mlft.IntegrarOnlineTask(tdrow, nvftstamp, "Descrição", False, "", 0, False, True)
        End If
        ' Integra contabilidade - Fim
        Dim nrft As Integer = cdata.getumvalorinteger($"select fno from ft where ftstamp = '{nvftstamp}'")
        Dim anoft As Integer = cdata.getumvalorinteger($"select ftano from ft (nolock) where ftstamp = '{nvftstamp}'")
        ' Cria o ficheiro PDF
        Dim Diretoria As String = HttpContext.Current.Server.MapPath("~").Trim() + "\pimages\anexos\faturas\"
        Dim NomeFicheiro As String = "FT" + CStr(docType) + "_" + anoft.ToString() + "_" + nrft.ToString() + ".pdf"
        Dim report As New FTreport(nvftstamp, 1)
        report.wrstamp = "3742018d68ab74f08eeeb5"
        With report.GetReportResultFromCache
            If .FilesResult.Any Then
                ' Guardar os bytes do relatório
                Dim pdf = .FilesResult(0).FileContents
                Dim oFileStream1 As System.IO.FileStream
                oFileStream1 = New System.IO.FileStream(
                    Diretoria + NomeFicheiro,
                    System.IO.FileMode.Create
                )
                oFileStream1.Write(pdf, 0, pdf.Length)
                oFileStream1.Close()
            End If
        End With
        Dim linkft As String = ""
        linkft = "http://192.168.5.4/Intranet_Triplex/pimages/anexos/faturas/" + NomeFicheiro
        Dim _myJSON As String
        _myJSON = "["
        _myJSON += "{""Ano"":""" + anoft.ToString() + """,""FatNum"":""" + nrft.ToString() + """,""PDF"":""" + linkft + """}"
        _myJSON += "]"
        Return _myJSON
    Catch ex1 As System.Exception
        Return "Ocorreu um erro ao criar o documento: " & ex1.Message
    End Try
Else
    Return "Não foi possível gravar o documento"
End If