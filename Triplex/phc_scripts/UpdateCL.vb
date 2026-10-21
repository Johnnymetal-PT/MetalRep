' AtualizaCL: Atualizar cliente existente via PHC (morada / codpost / localidade)
' Montar funcionalidade de leitura das variáveis recebidas por API
mstamp = "<root>" & mstamp & "</root>"
Dim stream As New System.IO.MemoryStream(Encoding.UTF8.GetBytes(mstamp))
Dim reader As System.Xml.XmlReader = New System.Xml.XmlTextReader(stream)
' Criação das variáveis
Dim nome As String = ""
Dim morada, localidade As String
morada = "" : localidade = ""
Dim codpostal As String
codpostal = ""
Dim telefone, email, telemovel As String
telefone = "" : email = "" : telemovel = ""
Dim pncont As String = ""
Dim ncont As String = ""
Dim no As Integer = 0
Dim pais As String = ""
Dim paisorigem As Integer = 1
Dim vendedor As String = ""
Dim vendedornr As Integer = 0
Dim condpag As String = ""
Dim tpstamp As String = ""
Dim codmotisencaoimp,descmotisencaoimp as String
codmotisencaoimp = "" : descmotisencaoimp = ""
Dim tabprecost as integer = 1
Dim _myJSONerro as String = ""
Dim _myJSON as String = ""
Dim column As String = ""
' Para cada elemento recebido
Do While (reader.Read())
  Select Case reader.NodeType
    Case System.Xml.XmlNodeType.Element
      column = reader.Name.ToLower()
    Case System.Xml.XmlNodeType.Text
      Dim value As String = reader.Value
      Select Case column
        Case "no"
          If IsNumeric(value) Then no = CInt(value)
        Case "ncont"
          ncont = value.Trim().ToUpperInvariant()
        Case "nome"
          nome = value
        Case "morada"
          morada = value
        Case "codpost"
          codpostal = value
        Case "localidade"
          localidade = value
        Case "pncont"
          pncont = value.Trim().ToUpperInvariant() 
          ' Valida se pais existe
          Dim dt_pais As DataTable = cdata.getdatatable("select nome,nomeabrv,ue from paises (nolock) where NOMEABRV = '" + value + "'")
          If dt_pais.haverows Then
            pais = dt_pais.rows(0).item("nome").toString()
            If dt_pais.rows(0).item("nomeabrv").toString() = "PT" Then
              paisorigem = 1
            ElseIf dt_pais.rows(0).item("nomeabrv").toString() <> "PT" And dt_pais.rows(0).item("ue").tostring() = True Then
              paisorigem = 2
            Else
              paisorigem = 3
            End If
          Else
            _myJSONerro = "["
 			_myJSONerro += "{""Mensagem"":""País não existe na tabela de países PHC.""}"
 			_myJSONerro += "]"
          End If
        Case "telefone"
          telefone = value
        Case "telemovel"
          telemovel = value
        Case "email"
          email = value
        Case "vendedornr"
          ' Valida se vendedor existe
			Dim tmpVend As Integer
			If Not Integer.TryParse(value, tmpVend) Then
        		_myJSONerro = "[{""Mensagem"":""Número de vendedor tem de ser numérico.""}]"
		 		Return _myJSONerro
			End If
			Dim dt_vendedor As DataTable = cdata.getdatatable("select cm3.cmdesc from cm3 (nolock) where cm='" + tmpVend.ToString() + "'")
			If dt_vendedor.HaveRows Then
  				vendedor = dt_vendedor.Rows(0).Item("cmdesc").ToString()
  				vendedornr = tmpVend
			Else
       			_myJSONerro = "[{""Mensagem"":""Vendedor não existe no PHC. Deve criar o vendedor primeiro no PHC com o mesmo número.""}]"
  				Return _myJSONerro
			End If
        Case "condpag"
          Dim dt_condpag As DataTable = cdata.getdatatable("select tpstamp from tp (nolock) where descricao ='" + value + "' And Tipo=1")
          'If dt_condpag.haverows Then
          If dt_condpag IsNot Nothing AndAlso dt_condpag.Rows.Count > 0 Then
            tpstamp = dt_condpag.rows(0).item("tpstamp").toString()
            condpag = value
          Else
            _myJSONerro = "["
 			_myJSONerro += "{""Mensagem"":""Condição de pagamento não existe no PHC.""}"
 			_myJSONerro += "]"
			return _myJSONerro
          End If
       
        Case "tabprecost"
      		tabprecost = value
     		 if tabprecost = 0 Then tabprecost=1
          
        Case "codmotisencao"
        
        Dim dt_mii As DataTable = cdata.getdatatable("select codigo,descricao from miseimp (nolock) where miseimp.codigo ='" + value.trim() + "'")
        If dt_mii.haverows And value.Trim() <> "" then
      		codmotisencaoimp = value.Trim().ToUpperInvariant()
          	descmotisencaoimp = dt_mii.rows(0).item("descricao").toString()
        Else
          	codmotisencaoimp = ""
        	descmotisencaoimp = ""
        	_myJSONerro = "["
          	_myJSONerro += "{""Mensagem"":""Código do motivo de isenção inválido""}"
			_myJSONerro += "]"
        	Return _myJSONerro
      End if 
      End Select
  End Select
Loop
' Normalização "SEM NIF"
If Trim(ncont.ToUpper()) = "SEM NIF" Then
  ncont = ""
End If
' Valida identificador para encontrar o cliente
If no = 0 AndAlso Trim(ncont) = "" Then
  _myJSONerro = "["
  _myJSONerro += "{""Mensagem"":""Tem de indicar o nº de cliente (no) ou o NIF (ncont) para atualizar.""}"
  _myJSONerro += "]"
	return _myJSONerro
End If
' Valida se há algo para atualizar (no teu caso, morada/codpost são o exemplo)
If Trim(morada) = "" AndAlso Trim(codpostal) = "" AndAlso Trim(localidade) = "" AndAlso _
   Trim(telefone) = "" AndAlso Trim(telemovel) = "" AndAlso Trim(email) = "" AndAlso _
   Trim(ncont) = "" AndAlso Trim(nome) = "" AndAlso vendedornr = 0 AndAlso Trim(condpag) = "" AndAlso Trim(pncont) = "" AndAlso _
   tabprecost = 0 AndAlso Trim(codmotisencaoimp) = "" Then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Não foram recebidos campos para atualizar.""}"
	_myJSONerro += "]"
	return _myJSONerro      
End If
' Validar Formato código postal PT - NNNN-NNN (só se vier pncont=PT e codpostal tiver sido enviado)
If pncont = "PT" AndAlso Trim(codpostal) <> "" Then
  Dim iTeste As Int32
  If codpostal.Trim().Equals(String.Empty) Then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal português não pode ser vazio. Tem de ter o formato NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro 
  End If
  If (codpostal.Length < 8) Then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal português tem de ter 8 carateres NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro 
  End If
  If Int32.TryParse(codpostal.Substring(0, 4).Trim, iTeste) = False Or codpostal.Substring(0, 4).Trim.Length < 4 Then
  	_myJSONerro = "["
        _myJSONerro += "{""Mensagem"":""Código postal português tem estar no formato NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro 
  End If
  If codpostal.IndexOf("-") <> 4 Then
  	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal português tem estar no formato NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro 
  End If
  If Int32.TryParse(codpostal.Substring(5, 3).Trim, iTeste) = False Or codpostal.Substring(5, 3).Trim.Length < 3 Then
  	_myJSONerro = "["
	_myJSONerro += "{""Mensagem"":""Código postal português tem estar no formato NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro 
  End If
  If (codpostal.Length > 8) AndAlso codpostal.Substring(8, 1).Trim.Length > 0 Then
  	_myJSONerro = "["
	_myJSONerro += "{""Mensagem"":""Código postal português tem estar no formato NNNN-NNN""}"
	_myJSONerro += "]"
	return _myJSONerro  
  End If
End If
' Encontrar o cliente
Dim usqlFind As String = ""
If no > 0 Then
      usqlFind = "select top 1 no, clstamp,ncont from cl (nolock) where no=" + no.ToString()
Else
      usqlFind = "select top 1 no, clstamp,ncont from cl (nolock) where ncont='" + ncont.Replace("'", "''") + "'"
End If
Dim dtFind As DataTable = cdata.getdatatable(usqlFind)
If Not dtFind.HaveRows Then
  	_myJSONerro = "["
	_myJSONerro += "{""Mensagem"":""Cliente não encontrado com os dados fornecidos.""}"
	_myJSONerro += "]"
	return _myJSONerro      
End If
Dim noCliente As Integer = CInt(dtFind.Rows(0).Item("no"))
Dim clstamp As String = dtFind.Rows(0).Item("clstamp").ToString()
' ... (após encontrares noCliente e clstamp)
'''Validar se pode atualizar nr contribuinte, verificar se tem docs certificados    
' Ler ncont atual da ficha do cliente
Dim ncontAtual As String = ""
ncontAtual = dtFind.Rows(0).Item("ncont").ToString().Trim()
Dim ncontNovo As String = Trim(ncont)
' Se foi enviado ncont e é diferente do atual, validar se há documentos certificados emitidos (FT/BO) para o ncont atual
If ncontNovo <> "" AndAlso String.Compare(ncontNovo, ncontAtual, True) <> 0 Then
  Dim ncontAtualSql As String = ncontAtual.Replace("'", "''")
  Dim usqlDocsCert As String =
    "select 1 where exists " &
    "(select bo.no from bo (nolock) " &
    " inner join ts (nolock) on bo.ndos=ts.ndos " &
    " inner join ts2 (nolock) on ts.tsstamp = ts2.ts2stamp " &
    " where ts.bdempresas = 'CL' and bo.no = " & noCliente.ToString() & " And bo.estab = 0 and ts2.assinadoc = 1) " &
    "or exists (select ft.no from ft (nolock) " &
    " inner join td (nolock) on ft.ndoc=td.ndoc " &
    " where ft.no = " & noCliente.ToString() & " and ft.estab = 0 and td.assinadoc = 1) " &
    "or exists (select rd.no from rd (nolock) " &
    " inner join tsrd (nolock) on rd.ndoc=tsrd.ndoc " &
    " where rd.no = " & noCliente.ToString() & " and rd.estab = 0 and tsrd.assinadoc = 1) " &
    "or exists (select re.no from re (nolock) " &
    " where re.no = " & noCliente.ToString() & " and re.estab = 0)"
  Dim dtDocsCert As DataTable = cdata.getdatatable(usqlDocsCert)
  If dtDocsCert IsNot Nothing AndAlso dtDocsCert.Rows.Count > 0 Then
	_myJSONerro = "["
	_myJSONerro += "{""Mensagem"":""Desculpe, mas não pode alterar o NIF numa ficha de cliente já existente e com documentos certificados já emitidos.""}"
	_myJSONerro += "]"
	return _myJSONerro        
  End If
End If
  
    
'''Fim da validação
Dim setsCl As New List(Of String)
' Só atualiza o que vier preenchido
If Trim(nome) <> "" Then setsCl.Add("nome='" & nome.Replace("'", "''") & "'")
If Trim(morada) <> "" Then setsCl.Add("morada='" & morada.Replace("'", "''") & "'")
If Trim(codpostal) <> "" Then setsCl.Add("codpost='" & codpostal.Replace("'", "''") & "'")
If Trim(localidade) <> "" Then setsCl.Add("local='" & localidade.Replace("'", "''") & "'")
If Trim(telefone) <> "" Then setsCl.Add("telefone='" & telefone.Replace("'", "''") & "'")
If Trim(telemovel) <> "" Then setsCl.Add("TLMVL='" & telemovel.Replace("'", "''") & "'")
If Trim(email) <> "" Then setsCl.Add("email='" & email.Replace("'", "''") & "'")
If Trim(ncont) <> "" Then setsCl.Add("ncont='" & ncont.Replace("'", "''") & "'")
If Trim(pncont) <> "" Then
  setsCl.Add("pncont='" & pncont.Replace("'", "''") & "'".ToUpper())
  setsCl.Add("pais=" & paisorigem.ToString())
End If
If vendedornr > 0 Then
  setsCl.Add("VENDEDOR=" & vendedornr.ToString())
  setsCl.Add("VENDNM='" & vendedor.Replace("'", "''") & "'")
End If
If Trim(condpag) <> "" Then
  setsCl.Add("tpdesc='" & condpag.Replace("'", "''") & "'")
  setsCl.Add("tpstamp='" & tpstamp.Replace("'", "''") & "'")
End If
                      
If tabprecost > 0 Then setsCl.Add("preco=" & tabprecost.ToString())
                        
If Trim(codmotisencaoimp) <> "" Then
  setsCl.Add("codmotiseimp='" & codmotisencaoimp.Replace("'", "''") & "'")
  setsCl.Add("motiseimp='" & descmotisencaoimp.Replace("'", "''") & "'")
End If
                        
                        
If setsCl.Count = 0 Then
  _myJSONerro = "["
  _myJSONerro += "{""Mensagem"":""Não foram recebidos campos para atualizar.""}"
  _myJSONerro += "]"
  return _myJSONerro
End If
Dim usqlUpdateCl As String =
  "update cl set " & String.Join(",", setsCl.ToArray()) &
  " where clstamp='" & clstamp.Replace("'", "''") & "'"
Dim usqlUpdateCl2 As String = ""
If Trim(pncont) <> "" Then
  usqlUpdateCl2 =
    "update cl2 set CODPAIS='" & pncont.Replace("'", "''") & "', DESCPAIS='" & pais.Replace("'", "''") & "'" &
    " where cl2stamp='" & clstamp.Replace("'", "''") & "'"
End If
Using tran = SqlHelp.GetNewConnection.BeginPhcTransaction("UpdateCL")
  cdata.getdatatable(usqlUpdateCl)
  If Trim(usqlUpdateCl2) <> "" Then cdata.getdatatable(usqlUpdateCl2)
  tran.Commit()
End Using
                     
_myJSON = "[{""Mensagem"":""Cliente atualizado com sucesso"",""Numero"":""" & noCliente & """}]"
Return _myJSON