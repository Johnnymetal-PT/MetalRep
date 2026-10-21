# DEWA: puxador que segue para o subcontratado

- **Tarefa:** #7782
- **Para:** reunião geral de 15/10/2026
- **Data:** 09/10/2026
- **Versão:** 1.0 (nota de apoio)
- **Base:** ensaios na base de teste da HMD (HMD_TESTE) e leitura da produção, a 09/10/2026. Nada foi alterado em produção.

---

## 1. Em duas linhas

O DEWA com puxador para o subcontratado **faz-se com configuração standard**, sem desenvolvimento. O que o impedia não era a lista de materiais: era uma configuração de **11 fornecedores subcontratados** (entre eles o Julião e o José Américo), que faz com que o Odoo nunca crie a ordem de subcontratação para eles.

## 2. O que a Nina pediu

Criar o DEWA: o artigo leva um puxador, e o puxador segue, junto com uma parte do artigo, para um fornecedor que a HMD subcontrata.

## 3. Como o DEWA está hoje

- O DEWA DESK e a DEWA CONSOLE são **kits**: juntam o corpo da peça (comprado ao Julião) e o puxador (comprado ao José Américo).
- As listas de subcontratação do corpo só levam as caixas. O puxador nunca vai para o Julião pelo Odoo.
- O puxador é escolhido na venda (atributo «Puxador», com 4 acabamentos).
- A base de teste não é igual à produção para este artigo: lá o atributo do puxador é de outro tipo, e a Nina deixou lá listas experimentais que não podem funcionar. Por isso os ensaios foram feitos em artigos novos, com a estrutura da produção.

## 4. O que ensaiámos

| Ensaio | O que fizemos | Resultado |
|---|---|---|
| **Desenho** | Pôr a subcontratação no **artigo acabado**, com o puxador como componente que depende do acabamento escolhido | A ordem de subcontratação leva **só o puxador escolhido** e as caixas |
| **Puxador por reposição** | O puxador é comprado ao José Américo, entra no stock da HMD e a HMD envia-o ao Julião | Funciona: o Odoo cria o movimento «Reposição para subcontratação» |
| **Puxador por envio direto** | O José Américo entrega o puxador diretamente ao Julião | Funciona: a compra é de tipo «Dropship Subcontractor», com entrega ao Julião |
| **Com a configuração atual dos fornecedores** | Os mesmos ensaios, sem alterar nada nos fornecedores | **Não nasce ordem de subcontratação** |

## 5. O ponto central: a configuração dos fornecedores

- Em 11 dos 15 fornecedores afetados, a **localização de fornecedor** está em «Inter-warehouse transit» (trânsito) em vez de «Partners/Vendors». São eles: Julião Vasques Brandão, José Américo Babo Nogueira, PVM, Serafim Dias Carneiro, Tábula, White Stone, Relaxvanguard, Fábrica Móveis Fontes, Décimas d'Emoções, Seratu's e M.G. Fernandes.
- O Odoo só cria a ordem de subcontratação quando o recibo vem de uma localização de fornecedor. Por isso, para estes fornecedores, nunca nasce.
- Isto vem da **importação inicial de fornecedores** (13/03/2025). Não foi nenhuma decisão recente.
- As únicas ordens de subcontratação que existem hoje em produção vêm de Ilogue, Industof e Paluma, que têm a localização certa.
- Quando pusemos o Julião e o José Américo em «Partners/Vendors», **na base de teste**, os ensaios funcionaram.
- **Consequência para a #7428:** as rotas de reposição e de envio direto aplicadas a 08/10 só produzem efeito nos fornecedores com a localização certa. Os outros 11 não geram subcontratação.

## 6. O que a HMD precisa de saber antes de corrigirmos em produção

Numa amostra dos 25 recibos concluídos mais recentes de cada grupo, **nenhum dos recibos de fornecedores em trânsito tem valorização de stock**, enquanto nos restantes fornecedores têm todos. Ou seja, as compras aos subcontratados afetados podem não estar a contar na valorização do stock.

Corrigir a localização, portanto, tem efeitos para lá da subcontratação:
- Passam a entrar na valorização de stock as compras futuras a esses fornecedores.
- Os recibos que estão em aberto agora continuam com a localização antiga.
- O histórico anterior não muda.

**Não propomos corrigir em produção sem a HMD (quem acompanha a contabilidade e o stock) validar.** Propomos mostrar o efeito na base de teste primeiro.

## 7. A solução para o DEWA

1. Corrigir a localização de fornecedor do Julião e do José Américo (e dos restantes subcontratados, depois de validado).
2. Passar a subcontratação para o **DEWA DESK e a DEWA CONSOLE** (artigo acabado), com o Julião como subcontratado.
3. A lista de subcontratação leva as caixas e o puxador, e o puxador só entra quando é o escolhido na venda.
4. Escolher como o puxador chega ao Julião: reposição (passa pela HMD) ou envio direto (o José Américo entrega).

Classificação: `Configuracao standard`, cobertura `TOTAL`, sujeita ao que a Nina confirmar abaixo.

## 8. Perguntas para a Nina

- Quem monta o puxador? É o Julião, ou a HMD?
- O puxador deve ir para o Julião antes de a peça seguir para o cliente? Se sim, passa pela HMD ou vai direto do José Américo?
- O Julião faz a peça completa sozinho, ou a peça segue para outro fornecedor? (Se segue, é o caso da cadeia de subcontratação da tarefa #7783.)
- O corpo do DEWA tem preço de compra 0 num fornecedor e 110 noutro. Qual vale?

## 9. Decisões esperadas na reunião

- [ ] A HMD concorda em corrigir a localização dos fornecedores, depois de ver o efeito na base de teste.
- [ ] Quem, na HMD, valida o efeito na valorização de stock.
- [ ] Reposição ou envio direto para o puxador.
- [ ] Autorização para migrar o DEWA DESK e a CONSOLE de kit para subcontratação.

## 10. O que ainda não está ensaiado

- A cadeia em que uma peça segue de um fornecedor para outro, com o transporte da HMD (tarefa #7783).
- A migração do DESK e da CONSOLE de kit para subcontratação, e o efeito nas encomendas em curso.
- A venda de uma variante sem puxador.

## 11. Para mostrar na reunião, se quiserem

Na base de teste ficaram os artigos «ZZ 7782 DEWA DESK» e componentes, as compras P00936 a P00939 e as ordens de subcontratação HMD/SBC1/00019 e HMD/SBC1/00020. Na base de teste, o Julião e o José Américo estão com a localização corrigida (o valor original era o trânsito), e vamos repô-los quando terminarmos.
