---
assunto: Projetos Essani — os dados já gravam, e três coisas que precisamos de vocês
em_resposta_a: RE: Projetos Essani (Ana Valente, 18/09 11:06)
para: Ana Valente <PREENCHER@essani.pt>
cc:
bcc:
---

Olá Ana,

Primeiro o que me perguntou: o erro era nosso, não seu, e peço desculpa. O Odoo estava a tratar a ficha da Essani como se fosse a de um cliente e a exigir campos que só fazem sentido num cliente, como o responsável comercial e o vendedor. Por muito que preenchesse, nunca ia conseguir gravar.

Já está corrigido e testado. Pode voltar a abrir Definições → Empresas → Essani e gravar os valores que já tinha preenchido — o NIF, o telefone e o email. Se puder, aproveite para mudar o formato de página de US Letter para A4, que é o formato em que saem os orçamentos. Se aparecer outro erro, mande-me o print como fez agora.

Aproveito para lhe dar o resto do ponto da situação de uma vez, em vez de andar a interromper-vos várias vezes. O circuito de protótipos está pronto e já dá para experimentar na base de testes, e a arrumação dos documentos dos artigos também já está feita. Para fechar esta fase e seguir para as seguintes, precisamos de três coisas vossas.

**1. Experimentar os protótipos**

Agora um protótipo cria-se a partir da oportunidade, de uma vez: o sistema dá-lhe a referência, cria o artigo com as especificações que combinaram com o cliente e o projeto com as etapas, e liga tudo. Se alguém mudar uma especificação, o gestor de projeto é avisado automaticamente.

Vai em anexo um guião com cinco passos para percorrerem. Há duas perguntas que são mesmo as importantes:

- As sete características que pusemos numa fonte de alimentação — tensão de entrada, tensão de saída, potência, corrente máxima, capacidade de carga, grau de proteção IP e notas do cliente — são as que combinam com o cliente? Falta alguma? Sobra alguma?
- Que tarefas é que um protótipo tem sempre, em cada etapa? Por agora o modelo traz as etapas, mas vem sem tarefas.

**2. Documentos dos artigos**

Já está criada a pasta **Artigos** nos Documentos, com uma sub-pasta por família de produto e etiquetas por tipo — fichas técnicas, certificados, manuais, desenhos. E as fichas técnicas já seguem sozinhas nos orçamentos: são 781 documentos que o vendedor deixa de andar à procura.

Uma nota sobre o desenho, porque é diferente do que imaginámos no início. Os documentos continuam guardados **no artigo**, não dentro da pasta. Testámos pô-los lá e descobrimos que os dois ficam presos ao mesmo ficheiro: apagar um documento da pasta apagava a ficha técnica do artigo. Como está, o site, os orçamentos e os protótipos vão todos buscar os documentos ao artigo, e ninguém os perde por engano.

Ficaram três coisas por decidir:

- Há **3360 documentos** que não aparecem nas páginas de produto do site. Devem aparecer, ou estão de fora de propósito?
- Os **351 certificados de conformidade** também devem seguir nos orçamentos, como as fichas técnicas?
- Há **5697 documentos** que ficaram sem artigo associado, por causa de uma falha na importação que entretanto corrigimos. Neste momento ninguém lhes chega — nem pelo site nem pelo Odoo. Vamos tentar recuperar os que tiverem a referência do artigo no nome do ficheiro; **podemos apagar os que sobrarem?**

**3. Manutenções — falta-nos informação**

Já instalámos os módulos de manutenção na base de testes. Para configurar precisamos de saber:

- que zonas internas querem cobrir;
- quem é o responsável de cada uma;
- de quanto em quanto tempo deve ser feita.

Os manuais ligamos depois, a cada equipamento.

**O que pedimos**

Se conseguirem experimentar os protótipos e responder aos pontos 2 e 3 até ao fim da próxima semana, era o ideal. Os pontos 1 e 2 são os que seguram a passagem para produção; o 3 pode vir depois, sem atrapalhar nada.

Se preferirem, fazemos a experiência em conjunto numa chamada — é só dizer.
