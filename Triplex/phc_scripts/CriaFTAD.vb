mstamp = "<root>" & mstamp & "</root>"
'Tranformação da string recebida pelo webservice em xml
Dim stream As New System.IO.MemoryStream(Encoding.UTF8.GetBytes(mstamp))
Dim reader As System.Xml.XmlReader = New System.Xml.XmlTextReader(stream)
'criação das variáveis, doctype é nº interno do document, clno é nº do cliente 
Dim docType, clNo As Integer
Dim formapag as String = "",descricao as String = ""
Dim mndoc as Integer,mnmdoc as String = "",midserie as String = ""
Dim cl_nome,cl_morada,cl_local,cl_codpost,cl_ncont,cl_codmotiseimp,cl_motiseimp as string
Dim cl_nib,cl_zona,cl_vendnm,cl_segmento,cl_tipo as string,cl_vendedor,cl_pais,cl_tabiva as Integer
Dim mvalor_base,mvalor,mvalor_iva,mvalor_total,mTxIVA as Decimal
Dim mollocal as String,mcontado,mtabiva as Integer
Dim mcmcc as Integer
Dim mcmccn as String
Dim column As String = ""
Do While (reader.Read())
  Dim newrowWithRefeQtt As DataRow
  Select Case reader.NodeType
  Case System.Xml.XmlNodeType.Element 'Início do elemento.
    column = reader.Name.ToLower
  Case System.Xml.XmlNodeType.Text 'texto/valor em cada elemento.
    Dim value As String = reader.Value
    Select Case column
    Case "doctype","no"
      If column = "no" Then
        Integer.TryParse(value, clNo)
        'Valida se cliente existe
        Dim dt_cl As DataTable = cdata.getdatatable("select no,nome,morada,local,codpost,ncont,nib,zona,vendedor,vendnm,segmento,tipo,pais,tabiva,codmotiseimp,motiseimp from cl (nolock) where cl.no='"+cStr(clNo)+
          "' and cl.estab=0")
        If dt_cl.HaveRows Then          
          cl_nome  = dt_cl.rows(0).item("nome")
          cl_morada  = dt_cl.rows(0).item("morada")
          cl_local  = dt_cl.rows(0).item("local")
          cl_codpost  = dt_cl.rows(0).item("codpost")
          cl_ncont  = dt_cl.rows(0).item("ncont")
          cl_nib  = dt_cl.rows(0).item("nib")
          cl_zona  = dt_cl.rows(0).item("zona")
          cl_vendedor  = dt_cl.rows(0).item("vendedor")
          cl_vendnm  = dt_cl.rows(0).item("vendnm")
          cl_segmento  = dt_cl.rows(0).item("segmento")
          cl_tipo  = dt_cl.rows(0).item("tipo")
          cl_pais  = dt_cl.rows(0).item("pais")
          cl_tabiva = dt_cl.rows(0).item("tabiva")
          cl_codmotiseimp = dt_cl.rows(0).item("codmotiseimp")
          cl_motiseimp = dt_cl.rows(0).item("motiseimp")
        Else
          return "O cliente não existe!!"
        End If
      ElseIf column = "doctype" Then
        Integer.TryParse(value, docType)
        'Valida se tipo documento fatura
        Dim dt_tsrd As DataTable = cdata.getdatatable("select * from tsrd (nolock) where ndoc='"+Cstr(docType)+"'")
        If dt_tsrd.HaveRows Then
          mndoc = dt_tsrd.rows(0).item("ndoc")
          mnmdoc = dt_tsrd.rows(0).item("nmdoc")
          midserie = dt_tsrd.rows(0).item("idserie")
          mcmcc = dt_tsrd.rows(0).item("cmcc")
          mcmccn = dt_tsrd.rows(0).item("cmccn")
        Else
          return "doctype não é válido!"
        End If
      End If
    Case "formapag"
      formapag = value
     ' IF formapag = "" Then
        'Return "A forma de pagamento é obrigatório"
      'End  If
      ''IF (formapag= "MB/Cartão de Crédito" Or formapag= "Numerário") Then
        
       ' Dim dt_bl2 As DataTable = cdata.getdatatable("select top 1 conta,noconta,banco from bl (nolock) where u_clinica='"+Cstr(clinica)+"' and u_formpag='" + formapag + "'")
       ' If dt_bl2.HaveRows Then          
       '   mollocal = dt_bl2.rows(0).item("banco").PadRight(11," ") + dt_bl2.rows(0).item("conta")
       '   mcontado = dt_bl2.rows(0).item("noconta")
       ' Else
       '   return "Não encontrei a conta de tesouraria associada à forma de pagamento " + formapag  + " com Id clínica " + Cstr(clinica) + "."
       ' end if
     ' Else
        ''Forma Cheque
        'If (formapag= "Cheque" ) Then
         
         ' Dim dt_blCH As DataTable = cdata.getdatatable("select top 1 conta,noconta,banco from bl (nolock) where U_PAGCH='" + formapag + "'")
          'If dt_blCH.HaveRows Then          
           ' mollocal = dt_blCH.rows(0).item("banco").PadRight(11," ") + dt_blCH.rows(0).item("conta")
           ' mcontado = dt_blCH.rows(0).item("noconta")
          'Else
          '  return "Não encontrei a conta de tesouraria associada à forma de pagamento cheque."
          'End If
       ' Else
          'Senão for nem MB nem Numerário nem Cheque
          
          'Dim dt_bl1 As DataTable = cdata.getdatatable("select top 1 conta,noconta,banco from bl (nolock) where u_formpag='" + formapag + "'")
          'If dt_bl1.HaveRows Then          
           ' mollocal = dt_bl1.rows(0).item("banco").PadRight(11," ") + dt_bl1.rows(0).item("conta")
           ' mcontado = dt_bl1.rows(0).item("noconta")
         ' Else
            'return "Não encontrei a conta de tesouraria associada à forma de pagamento  " + formapag           
          'End If
       ' End If 
     ' End If 
      
    Case "descricao"  
      descricao = value
      
    Case "valor" 
      Decimal.TryParse(value, mvalor)
      
     Case "tabiva"
        Decimal.TryParse(value, mtabiva)
      
    End Select
  End Select
Loop
'xcutil.sendmail("eduardo.santos@parametro.pt","it.ejsantos@gmail.com","Apos parametros", "")
'Verifica IVA 
Dim codIva As String = mtabiva.ToString().Replace("'", "''")
Dim dt_txIva As DataTable =
  cdata.getdatatable("SELECT TAXA FROM TAXASIVA (NOLOCK) WHERE CODIGO = '" & codIva & "'")
If dt_txIva IsNot Nothing AndAlso dt_txIva.Rows.Count > 0 Then
  mTxIVA = Convert.ToDecimal(dt_txIva.Rows(0)("TAXA"))
  mvalor_total = Convert.ToDecimal(mvalor)
  If mTxIVA > 0D Then
    Dim taxa As Decimal = mTxIVA / 100D
    'xcutil.sendmail("eduardo.santos@parametro.pt", "it.ejsantos@gmail.com", "taxa",
     '               taxa.ToString(System.Globalization.CultureInfo.InvariantCulture))
    mvalor_base = Decimal.Round(mvalor_total / (1D + taxa), 2, MidpointRounding.AwayFromZero)
    mvalor_iva = Decimal.Round(mvalor_total - mvalor_base, 2, MidpointRounding.AwayFromZero)
    cl_motiseimp = ""
    cl_codmotiseimp = 0
    'xcutil.sendmail("eduardo.santos@parametro.pt", "it.ejsantos@gmail.com", "mvalor_base",
     '               mvalor_base.ToString(System.Globalization.CultureInfo.InvariantCulture))
    'xcutil.sendmail("eduardo.santos@parametro.pt", "it.ejsantos@gmail.com", "mvalor_iva",
     '               mvalor_iva.ToString(System.Globalization.CultureInfo.InvariantCulture))
  Else
    mvalor_base = Decimal.Round(mvalor_total, 2, MidpointRounding.AwayFromZero)
    mvalor_iva = 0D
  End If
Else
  Return "Não foi possível obter a taxa de IVA (sem registos em TAXASIVA para o código)"
End If
Dim stampgerado As String = xcfox.u_stamp()
Dim rdataInsert As String = xcfox.dtosql(Today)
Dim rano As Integer = Year(Today)
Dim ndocSafe As String = CStr(mndoc).Replace("'", "''")
Dim sqlMaxRno As String =
"select top 1 isnull(rno,0) as rno, assinatura " &
"from rd (nolock) " &
"where ndoc = '" & ndocSafe & "' and rdano = '" & rano.ToString() & "' " &
"order by rno desc"
'xcutil.sendmail("eduardo.santos@parametro.pt", "it.ejsantos@gmail.com", "sqlMaxRno", sqlMaxRno)
Dim dtMaxRno As DataTable = cdata.GetDatatable(sqlMaxRno)
Dim maxRno As Integer = 0
Dim docAnterior As String = ""
If dtMaxRno IsNot Nothing AndAlso dtMaxRno.Rows.Count > 0 Then
  maxRno = CInt(dtMaxRno.Rows(0)("rno"))
  If Not IsDBNull(dtMaxRno.Rows(0)("assinatura")) Then
    docAnterior = CStr(dtMaxRno.Rows(0)("assinatura"))
  End If
End If
Dim nextRno As Integer = maxRno + 1
'xcutil.sendmail("eduardo.santos@parametro.pt", "it.ejsantos@gmail.com", "nextrno ---", nextRno.ToString())
Dim insertAdiantamento As PhcCommandBuilder= PhcCommandBuilder.CreateInsertInto("RD", True)
insertAdiantamento.AddInsertColumn("rdstamp",stampgerado)
insertAdiantamento.AddInsertColumn("ndoc",mndoc)
insertAdiantamento.AddInsertColumn("nmdoc",mnmdoc)
insertAdiantamento.AddInsertColumn("rno", nextrno)
insertAdiantamento.AddInsertColumn("rdata",rdataInsert)
insertAdiantamento.AddInsertColumn("rdano",rano)
insertAdiantamento.AddInsertColumn("no", clNo)
insertAdiantamento.AddInsertColumn("estab", 0)
insertAdiantamento.AddInsertColumn("nome", cl_nome)
insertAdiantamento.AddInsertColumn("morada",cl_morada)
insertAdiantamento.AddInsertColumn("local", cl_local)
insertAdiantamento.AddInsertColumn("codpost",cl_codpost)
insertAdiantamento.AddInsertColumn("ncont", cl_ncont)
insertAdiantamento.AddInsertColumn("nib",cl_nib)
insertAdiantamento.AddInsertColumn("zona", cl_zona)
insertAdiantamento.AddInsertColumn("vendedor",cl_vendedor)
insertAdiantamento.AddInsertColumn("vendnm", cl_vendnm)
insertAdiantamento.AddInsertColumn("segmento", cl_segmento)
insertAdiantamento.AddInsertColumn("tipo", cl_tipo)
insertAdiantamento.AddInsertColumn("pais", cl_pais)
insertAdiantamento.AddInsertColumn("moeda","EURO")
insertAdiantamento.AddInsertColumn("base",  EuroToEsc(mvalor_base) )
insertAdiantamento.AddInsertColumn("basemoeda", 0)
insertAdiantamento.AddInsertColumn("ebase", mvalor_base)
insertAdiantamento.AddInsertColumn("memissao", "EURO")
insertAdiantamento.AddInsertColumn("iva", mTxIVA)
insertAdiantamento.AddInsertColumn("tabiva", mtabiva)
insertAdiantamento.AddInsertColumn("ivav", EuroToEsc(mvalor_iva))
insertAdiantamento.AddInsertColumn("ivavmoeda", 0)
insertAdiantamento.AddInsertColumn("eivav", mvalor_iva)
insertAdiantamento.AddInsertColumn("total",EuroToEsc(mvalor_total))
insertAdiantamento.AddInsertColumn("etotal", mvalor_total)
insertAdiantamento.AddInsertColumn("totalmoeda", 0)
insertAdiantamento.AddInsertColumn("tptit",formapag)
insertAdiantamento.AddInsertColumn("olcodigo", "R10001")
insertAdiantamento.AddInsertColumn("contado", 0)
insertAdiantamento.AddInsertColumn("ollocal", "Caixa")
insertAdiantamento.AddInsertColumn("telocal","C")
insertAdiantamento.AddInsertColumn("descricao", descricao)
insertAdiantamento.AddInsertColumn("fref","")
insertAdiantamento.AddInsertColumn("ccusto", "")
insertAdiantamento.AddInsertColumn("ncusto","")
insertAdiantamento.AddInsertColumn("cm", mcmcc)
insertAdiantamento.AddInsertColumn("cmdesc", mcmccn)
insertAdiantamento.AddInsertColumn("cobranca", "")
insertAdiantamento.AddInsertColumn("cobrador", "")
insertAdiantamento.AddInsertColumn("rota", "")
insertAdiantamento.AddInsertColumn("cobrador", "")
insertAdiantamento.AddInsertColumn("chdata", Today)
insertAdiantamento.AddInsertColumn("moeda2", "EURO")
insertAdiantamento.AddInsertColumn("valorm2", 0)
insertAdiantamento.AddInsertColumn("setotal", 0)
insertAdiantamento.AddInsertColumn("ousrinis", xcuser.iniciais())
insertAdiantamento.AddInsertColumn("ousrhora", TimeOfDay())
insertAdiantamento.AddInsertColumn("ousrdata", Today)
insertAdiantamento.AddInsertColumn("usrinis",xcuser.iniciais())
insertAdiantamento.AddInsertColumn("usrdata",Today)
insertAdiantamento.AddInsertColumn("usrhora", TimeOfDay())
insertAdiantamento.AddInsertColumn("formapag", "1")
insertAdiantamento.AddInsertColumn("motiseimp", cl_motiseimp)
insertAdiantamento.AddInsertColumn("codmotiseimp",cl_codmotiseimp)
insertAdiantamento.AddInsertColumn("descregiva","PT")
insertAdiantamento.AddInsertColumn("idserie",midserie)
insertAdiantamento.AddInsertColumn("operext",0)
insertAdiantamento.AddInsertColumn("barcode","")
Dim systemEntryDate as string =  xcfox.dtosql(Today.toString()) 'Vai buscar o valor do ousrdata   ESTE VALOR NÃO VAI SER FIXO
systemEntryDate = systemEntryDate + "T" + TimeOfDay.toString() 'Vai buscar o valor do ousrhora    ESTE VALOR NÃO VAI SER FIXO
Dim cSel As String = "Select * from tsrd (nolock) where tsrd.ndoc= '" + Cstr(mndoc) + "'"
Dim tsrdcursor = cdata.GetDatatable(cSel)
Dim invoiceNo as String = tsrdcursor.rows(0).item("tiposaft").ToString.Trim + " " + rano.toString.Trim + tsrdcursor.rows(0).item("idserie").ToString.Trim + mndoc.Tostring.Trim + "/" + nextrno.ToString.Trim
'xcutil.sendmail("eduardo.santos@parametro.pt","it.ejsantos@gmail.com","invoiceNo ---", invoiceNo)
Dim grossTotalAux As Decimal = mvalor 'ESTE VALOR NÃO VAI SER FIXO
Dim grossTotal As String = grossTotalAux.ToString("##################0.00")
grossTotal = grossTotal.Replace(",", ".")
If Not grossTotal.Contains(".") Then
  grossTotal = grossTotal + ".00"
End If
'Dim sqlAssinatura As String ="select top 1 rd.assinatura from rd (nolock) where rd.ndoc = " + mndoc + $" and rd.rdano ={rano} and rd.rno = '"+ dtMaxRno.rows(0).item("rno").toString()+"'"
'Dim dtAssinatura = cdata.GetDatatable(sqlAssinatura)
'Dim docanterior as String =dtAssinatura.Rows(0).item("assinatura") 
Dim stringtohash as string = xcfox.dtosql(rdataInsert) + ";" + systemEntryDate + ";" + invoiceNo + ";" + grossTotal + ";" + docanterior
insertAdiantamento.AddInsertColumn("assinatura",AssinaturaRsaClass.HashAndSign(stringtohash))
insertAdiantamento.AddInsertColumn("versaochave",Sistema.VersaoChave)
'xcutil.sendmail("eduardo.santos@parametro.pt","it.ejsantos@gmail.com","stringtohash", stringtohash)
Dim result As Integer = insertAdiantamento.ExecuteNonQuery(True)
Dim _myJSON as String
DIm linkft as string = "" 
IF result=1
  '>>>>>>>>>>>>>>>>>>>>>>>>>> Integra contabilidade - Início <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
  Dim ll_Integra as string = cdata.getumvalorstring("AUTOML","TSRD", "ndoc='"+Cstr(mndoc)+"'")
  'xcutil.sendmail("eduardo.santos@parametro.pt","eduardo.santos@parametro.pt","Integra Online", ll_Integra)
  IF ll_Integra= True then
    dim tsrd = WebControlLib.TsrdRow.GetTsrdRowCache(mndoc)
    'xcutil.sendmail("eduardo.santos@parametro.pt","eduardo.santos@parametro.pt","rdstamp", stampgerado)
    ' PHCON
    ' A SÉRIE DE FATURAÇÃO TEM DE TER CONTABILIDADE ONLINE
    ' USER contabilidade Web
    Mlrd.IntegrarOnlineTask(tsrd, stampgerado , "Descrição", True, "", 0, False)
    'xcutil.sendmail("eduardo.santos@parametro.pt","eduardo.santos@parametro.pt","result", tes)
  end if
  '>>>>>>>>>>>>>>>>>>>>>>>>>> Integra contabilidade - Fim <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
  'Cria o ficheiro PDF
  Dim Diretoria as String = HttpContext.Current.Server.MapPath("~").trim + "\pimages\Anexos\Adiantamentos\"
  dim NomeFicheiro as string = "FTAD"+ Cstr(mndoc) + "_" + rano.toString()+ "_" + nextrno.tostring + ".pdf"
  dim report as new RDreport(stampgerado, mndoc)
  report.wrstamp = "4b4fe68b95c6044fb173ce"
  with report.GetReportResultFromCache
  if.FilesResult.any
    ' Guardar os Bytes do Relatório
    dim pdf =.FilesResult(0).FileContents
    Dim oFileStream1 As System.IO.FileStream
    oFileStream1 = New System.IO.FileStream(Diretoria + NomeFicheiro, System.IO.FileMode.Create)
    oFileStream1.Write(pdf, 0, pdf.Length)
    oFileStream1.Close()
  end if
end with
linkft = "http://192.168.5.4/Intranet_Triplex/pimages/anexos/adiantamentos/" + NomeFicheiro
_myJSON = "["
_myJSON += "{""Ano"":"""+ rano.tostring +""",""FT_Adiantamento"":"""+ nextrno.tostring +""",""PDF"":"""+linkft+"""}"
_myJSON += "]"
else
_myJSON = "["
_myJSON += "{""Error"":""Não se pode gravar ao adiantamento"",""PDF"":""""}"
_myJSON += "]"
end if
return _myJSON