# Manual de Integração — Scripts PHC (VB.NET)

Esta pasta contém os códigos fonte dos scripts executados no **PHC CSWeb** (via método SOAP `RunCode`) para a integração com o Odoo 17.

## Scripts Incluídos

1. **[CriaCL.vb](file:///c:/Projetos/Triplex/phc_scripts/CriaCL.vb)**: Criar cliente/parceiro no PHC.
2. **[UpdateCL.vb](file:///c:/Projetos/Triplex/phc_scripts/UpdateCL.vb)**: Atualizar dados de cliente existente.
3. **[CriaFT.vb](file:///c:/Projetos/Triplex/phc_scripts/CriaFT.vb)**: Criar Faturas / Faturas-Recibo e processar a regularização de adiantamentos.
4. **[CriaFTAD.vb](file:///c:/Projetos/Triplex/phc_scripts/CriaFTAD.vb)**: Criar Recebimento de Adiantamento (tabela `RD`) e assinar digitalmente (SAFT).
5. **[CriaFTGT.vb](file:///c:/Projetos/Triplex/phc_scripts/CriaFTGT.vb)**: Criar Guia de Transporte (tabela `FT`, `doctype=11`) com dados de transporte e descarga.

---

## ⚠️ Checklist para Migração (Passos para Novo Cliente)

### 1. Criar Campos de Utilizador (UDFs) no PHC Destino
No script **`CriaFTGT`** (Guia de Transporte), os dados de descarga são guardados em campos personalizados da tabela **`EFT3`**. Garanta que cria os seguintes campos antes de migrar:
* `u_dmorada` (Morada de Descarga) - varchar(55)
* `u_dlocal` (Localidade de Descarga) - varchar(43)
* `u_dcodpost` (Código Postal de Descarga) - varchar(45)
* `u_dpais` (Nome do País de Descarga) - varchar(55)

### 2. Validar Limites de Caracteres (Diferenças Odoo vs PHC)
Os limites no Odoo já foram ajustados nos módulos para coincidir com as validações do PHC (evitando erros de sincronização):
* **Matrícula:** O Odoo agora trunca e envia automaticamente até **12 caracteres** (coincidindo com o limite do script `CriaFTGT`).
* **Morada de Descarga:** O Odoo agora trunca e envia automaticamente até **55 caracteres** (coincidindo com o limite do script `CriaFTGT`).

### 3. Estrutura de Diretórios e Permissões (Servidor IIS/PHC)
No servidor onde corre a API PHC CSWeb, garanta que os seguintes diretórios existem dentro da pasta da aplicação Web (tipicamente em `...\pimages\anexos\`) e têm permissões de **Escrita/Gravação** para o utilizador do Application Pool:
* `...\pimages\anexos\faturas\`
* `...\pimages\anexos\adiantamentos\`
* `...\pimages\anexos\guiastransporte\`

### 4. Assinatura Digital e Chaves SAFT
O script **`CriaFTAD`** calcula a assinatura fiscal diretamente por código via `AssinaturaRsaClass.HashAndSign`.
* Certifique-se de que a série e a chave privada do PHC destino estão ativas e atualizadas.
* Teste a gravação de um adiantamento no novo ambiente para garantir que a assinatura digital cumpre os requisitos legais e que a versão da chave (`Sistema.VersaoChave`) é válida.

### 5. Configuração das Taxas de IVA
A integração envia o código da tabela de IVA do Odoo para o PHC. Garanta que na nova base de dados PHC, a tabela `TAXASIVA` contém os mesmos códigos que os configurados na ficha de impostos no Odoo.
