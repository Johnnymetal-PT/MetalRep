/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function() {
    console.log("Bank Import Custom Module loaded - Extended version");
    
    // Função para verificar se estamos em contexto bancário
    function isBankContext() {
        try {
            const url = window.location.href;
            const breadcrumbs = document.querySelector('.o_breadcrumb');
            const breadcrumbText = breadcrumbs ? breadcrumbs.textContent : '';
            const pageTitle = document.title || '';
            
            // Verifica se estamos no Dashboard de Accounting com um Journal bancário
            let isDashboardWithBank = false;
            try {
                isDashboardWithBank = breadcrumbText.includes('Dashboard') && 
                                        (document.querySelector('[title*="Bank"]') ||
                                         // Verifica se há um card/record com "Bank" ou "Cash" no texto
                                         Array.from(document.querySelectorAll('.o_kanban_record')).some(el => 
                                             el.textContent.includes('Bank') || el.textContent.includes('Cash')
                                         ) ||
                                         Array.from(document.querySelectorAll('.o_kanban_card_header_title')).some(el => 
                                             el.textContent.includes('Bank') || el.textContent.includes('Cash')
                                         ) ||
                                         Array.from(document.querySelectorAll('.oe_kanban_details strong')).some(el => 
                                             el.textContent.includes('Bank') || el.textContent.includes('Cash')
                                         ));
            } catch (e) {
                // Se houver erro na verificação do dashboard, assume false
                isDashboardWithBank = false;
            }
            
            // Verifica vários indicadores de contexto bancário - MAIS ESPECÍFICO
            return (
                // Dashboard com Journal bancário
                isDashboardWithBank ||
                // Contexto original: importação de bank statement lines
                (url.includes('/import') && url.includes('active_model=account.bank.statement.line')) ||
                // Dashboard com Bank Reconciliation no breadcrumb
                breadcrumbText.includes('Bank Reconciliation') ||
                // URL contém referências específicas a bank statements
                url.includes('model=account.bank.statement') ||
                url.includes('action=account.action_bank_statement') ||
                url.includes('account.bank.statement.line') ||
                // Verifica se há elementos específicos de reconciliação bancária
                document.querySelector('[data-model="account.bank.statement.line"]') !== null ||
                document.querySelector('.account_bank_statement_line_list') !== null ||
                document.querySelector('.o_bank_rec_st_line') !== null ||
                document.querySelector('.o_bank_rec_widget') !== null
            );
        } catch (error) {
            console.error("Error in isBankContext:", error);
            return false;
        }
    }
    
    // Função para verificar se é um botão de upload/import bancário
    function isBankUploadButton(element) {
        // IMPORTANTE: Só considerar elementos clicáveis reais
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        const link = element.tagName === 'A' ? element : element.closest('a');
        const menuItem = element.closest('.dropdown-item') || element.closest('[role="menuitem"]');
        
        // Se não é nenhum elemento clicável, retorna false
        const targetElement = button || link || menuItem;
        if (!targetElement) return false;
        
        // Verifica se o elemento está realmente visível e habilitado
        if (targetElement.disabled || targetElement.style.display === 'none' || 
            targetElement.style.visibility === 'hidden') {
            return false;
        }
        
        const elementText = (targetElement.textContent || '').trim();
        const elementTitle = (targetElement.getAttribute('title') || '').trim();
        const elementName = (targetElement.getAttribute('name') || '').trim();
        const elementHref = (targetElement.getAttribute('href') || '').trim();
        
        // Debug específico para Upload
        if (elementText === 'Upload' || elementText.includes('Upload')) {
            console.log("DEBUG Upload Button Check:");
            console.log("  Element text:", elementText);
            console.log("  Element tag:", targetElement.tagName);
            console.log("  Is Button?", targetElement.tagName === 'BUTTON');
            console.log("  Has bank elements?", {
                bankRec: !!document.querySelector('.o_bank_rec_widget'),
                statementLine: !!document.querySelector('[data-model="account.bank.statement.line"]'),
                urlBankRec: window.location.href.includes('bank_rec'),
                urlBankStatement: window.location.href.includes('account.bank.statement'),
                breadcrumb: document.querySelector('.o_breadcrumb')?.textContent || ''
            });
        }
        
        // Lista mais específica de palavras-chave - MATCH EXATO
        const uploadKeywords = ['Upload', 'Upload Data File', 'Import records', 'Import File'];
        const hasExactUploadKeyword = uploadKeywords.some(keyword => {
            // Para "Import records", verifica se o texto contém exatamente isso
            if (keyword === 'Import records') {
                return elementText.includes(keyword) && 
                       (targetElement.tagName === 'BUTTON' || targetElement.tagName === 'A');
            }
            // Para "Upload", verifica se é um botão em contexto apropriado
            if (keyword === 'Upload') {
                // Verifica se é um botão Upload
                const isUploadButton = elementText === keyword && targetElement.tagName === 'BUTTON';
                
                if (isUploadButton) {
                    // Verifica se está em contexto de reconciliação bancária ou dashboard
                    const breadcrumb = document.querySelector('.o_breadcrumb')?.textContent || '';
                    const inBankContext = breadcrumb.includes('Bank Reconciliation') ||
                                         breadcrumb.includes('Dashboard') ||
                                         document.querySelector('.o_bank_rec_widget') ||
                                         document.querySelector('[data-model="account.bank.statement.line"]') ||
                                         document.querySelector('.o_list_view[data-model="account.bank.statement.line"]') ||
                                         window.location.href.includes('bank_rec') ||
                                         window.location.href.includes('account.bank.statement') ||
                                         window.location.href.includes('journal');
                    
                    console.log("Upload button detected, in bank context?", inBankContext);
                    return inBankContext;
                }
                return false;
            }
            // Para outros, match exato
            return elementText === keyword || 
                   elementTitle === keyword ||
                   elementName === keyword;
        });
        
        // Verifica classes muito específicas
        const hasSpecificUploadClass = targetElement.classList.contains('o_button_upload') || 
                                       targetElement.classList.contains('o_import_button') ||
                                       targetElement.classList.contains('o_list_button_import');
        
        // Só retorna true se houver match exato
        return hasExactUploadKeyword || hasSpecificUploadClass;
    }
    
    // Função para verificar se é um upload que NÃO devemos interceptar
    function isNonBankUpload(element) {
        const url = window.location.href;
        const elementText = element.textContent || '';
        
        // Lista de contextos que NÃO devemos interceptar
        const excludedContexts = [
            'res.partner',  // Upload de contatos
            'product.template',  // Upload de produtos
            'account.move',  // Upload de faturas (mas não bank statements)
            'hr.employee',  // Upload de funcionários
            'stock.',  // Qualquer upload relacionado a estoque
            'sale.',  // Uploads de vendas
            'purchase.',  // Uploads de compras
            'mrp.',  // Uploads de manufatura
        ];
        
        // Verifica se estamos em um contexto excluído
        const inExcludedContext = excludedContexts.some(context => 
            url.includes(context) || 
            url.includes(context.replace('.', '_'))
        );
        
        // Palavras-chave que indicam que NÃO é importação bancária
        const nonBankKeywords = ['Product', 'Contact', 'Employee', 'Invoice', 'Sale', 'Purchase', 'Inventory'];
        const hasNonBankKeyword = nonBankKeywords.some(keyword => elementText.includes(keyword));
        
        return inExcludedContext || hasNonBankKeyword;
    }
    
    // Monitora cliques no documento
    document.addEventListener('click', function(e) {
        const target = e.target;
        const targetText = target.textContent || '';
        const closestLink = target.closest('a');
        const closestButton = target.closest('button');
        
        // Debug logging para o Dashboard Import File
        if (targetText.includes('Import File') || (closestLink && closestLink.textContent.includes('Import File'))) {
            console.log("DEBUG: Import File clicked");
            console.log("DEBUG: Is Bank Context?", isBankContext());
            console.log("DEBUG: Current breadcrumb:", document.querySelector('.o_breadcrumb')?.textContent);
            console.log("DEBUG: Dashboard elements found:", {
                hasBank: Array.from(document.querySelectorAll('.o_kanban_record')).some(el => 
                    el.textContent.includes('Bank') || el.textContent.includes('Cash')
                ),
                hasDashboard: document.querySelector('.o_breadcrumb')?.textContent?.includes('Dashboard')
            });
        }
        
        // Interceptação especial para "Import File" no Dashboard
        // APENAS se clicar diretamente no link/botão "Import File"
        if (closestLink && closestLink.textContent?.trim() === 'Import File' &&
            document.querySelector('.o_breadcrumb')?.textContent?.includes('Dashboard')) {
            
            console.log("Import File link in Dashboard clicked!");
            
            // Verifica se há um journal bancário no dashboard
            const hasBankJournal = Array.from(document.querySelectorAll('.o_kanban_record')).some(el => 
                el.textContent.includes('Bank') || el.textContent.includes('Cash')
            );
            
            if (hasBankJournal) {
                console.log("Bank journal found in Dashboard - intercepting!");
                
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                // Abre o wizard de importação bancária
                if (window.odoo && window.odoo.__WOWL_DEBUG__) {
                    const env = window.odoo.__WOWL_DEBUG__.root.env;
                    if (env && env.services && env.services.action) {
                        env.services.action.doAction({
                            type: 'ir.actions.act_window',
                            res_model: 'bank.statement.import.wizard',
                            view_mode: 'form',
                            target: 'new',
                            views: [[false, 'form']],
                            name: 'Import Bank Statement',
                            context: {
                                default_bank_context: true,
                            }
                        });
                    }
                }
                
                return false;
            }
        }
        
        // Verificação especial para botão Upload
        const buttonElement = target.closest('button');
        if (buttonElement && buttonElement.textContent?.trim() === 'Upload') {
            console.log("Upload button clicked - checking context...");
            
            // Verifica se é um botão Upload em contexto bancário
            if (isBankUploadButton(target)) {
                console.log("Upload button in bank context - intercepting!");
                
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                // Abre o wizard de importação bancária
                if (window.odoo && window.odoo.__WOWL_DEBUG__) {
                    const env = window.odoo.__WOWL_DEBUG__.root.env;
                    if (env && env.services && env.services.action) {
                        env.services.action.doAction({
                            type: 'ir.actions.act_window',
                            res_model: 'bank.statement.import.wizard',
                            view_mode: 'form',
                            target: 'new',
                            views: [[false, 'form']],
                            name: 'Import Bank Statement',
                            context: {
                                default_bank_context: true,
                            }
                        });
                        console.log("Wizard action dispatched for Upload button");
                    }
                }
                
                return false;
            }
        }
        
        // Verificação normal para outros casos
        // Primeira verificação: não é um upload não-bancário
        if (isNonBankUpload(target)) {
            console.log("Non-bank upload detected - not intercepting");
            return; // Deixa o evento continuar normalmente
        }
        
        // Segunda verificação: estamos em contexto bancário
        if (isBankContext()) {
            // Terceira verificação: é um botão de upload/import ESPECÍFICO
            if (isBankUploadButton(target)) {
                console.log("Bank upload/import button detected!");
                console.log("Element clicked:", target);
                console.log("Button/Link found:", target.closest('button') || target.closest('a'));
                
                e.preventDefault();
                e.stopPropagation();
                
                console.log("Opening Bank Statement Import Wizard");
                
                // Usa o serviço de action do Odoo
                if (window.odoo && window.odoo.__WOWL_DEBUG__) {
                    const env = window.odoo.__WOWL_DEBUG__.root.env;
                    if (env && env.services && env.services.action) {
                        env.services.action.doAction({
                            type: 'ir.actions.act_window',
                            res_model: 'bank.statement.import.wizard',
                            view_mode: 'form',
                            target: 'new',
                            views: [[false, 'form']],
                            name: 'Import Bank Statement',
                            context: {
                                default_bank_context: true,
                            }
                        });
                        console.log("Wizard action dispatched");
                    }
                } else {
                    // Fallback para versões anteriores do Odoo
                    console.warn("Could not access Odoo action service - trying alternative method");
                }
                
                return false;
            }
        }
    }, true); // Use capture phase para interceptar antes de outros handlers
    
    // Monitora também mudanças de menu/ação para detectar contexto bancário
    const observer = new MutationObserver(function(mutations) {
        try {
            // Re-verifica contexto quando DOM muda
            if (isBankContext()) {
                // console.log("Bank context detected after DOM change");
            }
        } catch (error) {
            console.error("Error in MutationObserver:", error);
        }
    });
    
    // Observa mudanças no body
    try {
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });
    } catch (error) {
        console.error("Error setting up MutationObserver:", error);
    }
});