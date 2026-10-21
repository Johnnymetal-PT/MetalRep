' Montar funcionalidade de leitura das variáveis recebidas por API
mstamp = "<root>" & mstamp & "</root>"
Dim stream As New System.IO.MemoryStream(Encoding.UTF8.GetBytes(mstamp))
Dim reader As System.Xml.XmlReader = New System.Xml.XmlTextReader(stream)
' Criação das variáveis
Dim nome As String = ""
Dim morada,codpost,localidade,pais,condpag,tpstamp As String 
morada = "" : codpost = "" : pais = "" : condpag = "" : tpstamp = ""
Dim telefone,email,telemovel As String 
telefone = "" : email = "" : telemovel = ""
Dim codpostal as String = ""
Dim paisorigem as integer = 1 
Dim pncont,ncont As String
pncont = "" : ncont = ""
Dim vendedor as String = ""
Dim vendedornr as integer = 0
Dim tabprecost as integer = 1
Dim codmotisencaoimp,descmotisencaoimp as String
codmotisencaoimp = "" : descmotisencaoimp = ""
Dim clstamp as string=""
Dim no as string = ""
Dim _myJSONerro,_myJSON as String
Dim column As String = ""
' obter estrutura de dados da tabela cl e cl2 a usar
Dim clTable = PhcCommandBuilder.
CreateSelect("*").
From("cl").
GetSqlResultOnlySchema(Of SqlChangedRow)(False)
Dim cl2Table = PhcCommandBuilder.
CreateSelect("*").
From("cl2").
GetSqlResultOnlySchema(Of SqlChangedRow)(False)
' Para cada elemento recebido
Do While (reader.Read())
  Select Case reader.NodeType
  Case System.Xml.XmlNodeType.Element 'Início do elemento.
    column = reader.Name.ToLower
  Case System.Xml.XmlNodeType.Text 'texto/valor em cada elemento.
    Dim value As String = reader.Value
    Select Case column
    case "ncont"
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
      'Valida se pais existe 
      Dim dt_pais As DataTable = cdata.getdatatable("select nome,nomeabrv,ue from paises (nolock) where NOMEABRV = '"+value+"'")
      IF dt_pais.haverows Then
        pais = dt_pais.rows(0).item("nome").toString()
        'pncont = dt_pais.rows(0).item("nomeabrv").toString()
        'pais de origem
        Dim isUE As Boolean = Convert.ToBoolean(dt_pais.Rows(0)("ue"))
        IF dt_pais.rows(0).item("nomeabrv").toString()="PT" then
          paisorigem = 1 
        ElseIf dt_pais.rows(0).item("nomeabrv").toString()<>"PT" And isUE = True then
          paisorigem = 2
        Else
          paisorigem = 3
        End if
      Else 
        _myJSONerro = "["
        _myJSONerro += "{""Mensagem"":""País não existe na tabela de países PHC""}"
        _myJSONerro += "]"
        Return _myJSONerro
      End if
    Case "telefone"
      telefone = value
    case "telemovel"
      telemovel = value
    case "email"
      email = value 
    case "vendedornr"
      'Valida se vendedor existe
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
      IF dt_condpag.haverows then
      	tpstamp = dt_condpag.rows(0).item("tpstamp").toString()
        condpag = value
      else
        tpstamp=""
        condpag = ""
        _myJSONerro = "["
  		_myJSONerro += "{""Mensagem"":""Condição de pagamento não existe no PHC.""}"
		_myJSONerro += "]"
        Return _myJSONerro
      End if      
     
    case "tabprecost"
      tabprecost = value
      if tabprecost = 0 Then tabprecost = 1
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
IF nome.Trim() = "" then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Nome é de preenchimento obrigatório""}"
    _myJSONerro += "]"
    Return _myJSONerro 
END IF
  IF morada.Trim() = "" Then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Morada é de preenchimento obrigatório""}"
    _myJSONerro += "]"
    Return _myJSONerro    
END if
IF pncont.Trim()="PT" And codpostal.Trim() = "" Then
    _myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal é de preenchimento obrigatório""}"
    _myJSONerro += "]"
    Return _myJSONerro
END IF
'IF condpag = "" Then
   ' _myJSONerro = "["
    '_myJSONerro += "{""Mensagem"":""Condição de pagamento é de preenchimento obrigatório""}"
   ' _myJSONerro += "]"
   ' Return _myJSONerro
'END IF
IF trim(ncont.toUpper())="SEM NIF" Then
  ncont = ""
END If
'Validar Formato código postal PT - NNNN-NN
IF pncont="PT"
  Dim iTeste As Int32
  Dim sCodigoPostal As String = codpostal
  If codpostal.Trim().Equals(String.Empty) Then
	_myJSONerro = "["
      _myJSONerro += "{""Mensagem"":""Código postal não pode ser vazio.Tem de ter o formato NNNN-NNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
  If (codpostal.Length < 8) Then
	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal tem de ter 8 carateres NNNN-NNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
  If Int32.TryParse(codpostal.Substring(0, 4).Trim, iTeste) = False Or codpostal.Substring(0, 4).Trim.Length < 4 Then
   	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal PT tem de ter o formato NNNN-NNNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
  If codpostal.IndexOf("-") <> 4 Then
       	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal PT tem de ter o formato NNNN-NNNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
  If Int32.TryParse(codpostal.Substring(5, 3).Trim, iTeste) = False Or codpostal.Substring(5, 3).Trim.Length < 3 Then
       	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal PT tem de ter o formato NNNN-NNNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
  If (codpostal.Length > 8) AndAlso codpostal.Substring(8, 1).Trim.Length > 0 Then
   	_myJSONerro = "["
    _myJSONerro += "{""Mensagem"":""Código postal PT tem de ter o formato NNNN-NNNN""}"
	_myJSONerro += "]"
    Return _myJSONerro
  End If
END If
'''''
'xcutil.sendmail("eduardo.santos@parametro.pt", "eduardo.santos@parametro.pt","vendedor:" + cstr(vendedorNr) ,"" , false)
' Gerar novo stamp
Dim stamp = xcfox.u_stamp
Dim clRow = clTable.GetNewRow
Dim cl2Row = cl2Table.GetNewRow
Dim integraCL As New ClFlInt(clRow.ToWrapper)
Dim cl As New ClFormClass(clRow.ToWrapper, cl2Row.ToWrapper)
' Criar os valores por defeito para a tabela. Esta função utiliza o parâmetro do desktop: Procura furos na numeração dos clientes
cl.ValoresPorDefeitoAoIntroduzir(Normalform.EstadoDoMainForm.Adicionando)
clRow("clstamp") = stamp
cl2Row("cl2stamp") = stamp
clRow("nome") = nome
clstamp=stamp
clRow("morada") = morada
clRow("codpost") = codpostal
clRow("local") = localidade
clRow("telefone") = telefone
clRow("TLMVL") = telemovel
clRow("email") = email
clRow("pncont") = trim(pncont.toUpper())
clRow("ncont") = trim(ncont.toUpper())
clRow("pais") = paisorigem
clRow("VENDEDOR") = vendedornr
clRow("VENDNM") = vendedor
clRow("tpdesc") = condpag
clRow("tpstamp") = tpstamp
clRow("preco")   = tabprecost
clRow("codmotiseimp") = codmotisencaoimp
clRow("motiseimp") = descmotisencaoimp
  
'Criar contas na contabilidade
'cl.SetContasSNC()
cl2Row("CODPAIS") = trim(pncont.toUpper())
cl2Row("DESCPAIS") = pais
  
'integraCL.IntegraOnline()
' Validar Nº contribuinte
'If Not XcUtil.CheckNCont(clRow.ItemToString("ncont")) Then
'Throw New PhcException("O {0} está mal preenchido. O check-digit não condiz. Verifique se o número que está a introduzir está correto e não se esqueça que o número deverá possuir 9 dígitos e não pode conter espaços.".FormatWith(cparas.ge_NomeparaNIFextenso()), cEnums.TipoDeMensagem.Info)
'End If
' Gerar transação e inserir em ambas as tabelas
Using tran = SqlHelp.GetNewConnection.BeginPhcTransaction("CreateNewCL")
clRow.Insert(True)
cl2Row.Insert(True)
tran.Commit()
End Using
dim usql as string = "select no from cl (nolock) where clstamp='"+clstamp+"'"
Dim dt As DataTable = cdata.getdatatable(usql)
If dt.HaveRows Then
no= dt.rows(0).item("no").toString()
End If
_myJSON = "[{""Mensagem"":""O cliente criado programaticamente no PHC "",""Numero"":""" & no & """,""Nome"":""" & nome & """}]"
Return _myJSON