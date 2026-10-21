/** @odoo-module ignore **/

// Usar a diretiva "ignore" para evitar transpilação
(function() {
    'use strict';
    
    console.log("🎯 Import Numerator - Iniciando...");
    
    // Variáveis globais para controle
    var nextCustomerNumber = null;
    var nextSupplierNumber = null;
    var isProcessing = false;
    
    // Função para obter próximo número via API
    function getNextNumber(type) {
        console.log('📡 Chamando API para obter próximo número:', type);
        
        // Para Odoo, precisamos do CSRF token
        var csrfToken = document.querySelector('meta[name="csrf-token"]');
        var headers = {
            'Content-Type': 'application/json',
        };
        
        if (csrfToken) {
            headers['X-CSRF-Token'] = csrfToken.content;
        }
        
        // Usar formato JSON-RPC do Odoo
        var payload = {
            jsonrpc: "2.0",
            method: "call",
            params: {
                type: type
            },
            id: Math.floor(Math.random() * 1000000)
        };
        
        return fetch('/bank_statement_import_custom/get_next_number', {
            method: 'POST',
            headers: headers,
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        })
        .then(response => {
            console.log('📨 Resposta recebida:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📦 Dados da API:', data);
            
            // Odoo retorna em formato JSON-RPC
            if (data.result && data.result.next_number) {
                console.log('✅ Próximo número ' + type + ':', data.result.next_number);
                return data.result.next_number;
            } else if (data.error) {
                console.error('❌ Erro da API:', data.error);
                return 1; // Começar do 1 se houver erro
            } else {
                console.warn('⚠️ Resposta inesperada:', data);
                return 1;
            }
        })
        .catch(error => {
            console.error('❌ Erro ao obter próximo número:', error);
            // Fallback: começar do 1
            return 1;
        });
    }
    
    // Função para detectar tipo de importação
    function detectImportType() {
        var isCustomer = false;
        var isSupplier = false;
        
        console.log('🔍 Detectando tipo de importação...');
        
        // -1. VERIFICAR CONTEXTO ARMAZENADO DO CLIQUE DO BOTÃO
        var storedContext = sessionStorage.getItem('import_context_type');
        if (storedContext) {
            console.log('📌 Contexto armazenado do clique:', storedContext);
            if (storedContext === 'customer') {
                isCustomer = true;
                console.log('✅ Detectado como CLIENTE pelo contexto do clique');
                // Limpar após usar
                sessionStorage.removeItem('import_context_type');
                return { isCustomer: true, isSupplier: false };
            } else if (storedContext === 'supplier') {
                isSupplier = true;
                console.log('✅ Detectado como FORNECEDOR pelo contexto do clique');
                // Limpar após usar
                sessionStorage.removeItem('import_context_type');
                return { isCustomer: false, isSupplier: true };
            }
        }
        
        // 0. VERIFICAR HASH E PARÂMETROS DA URL (Odoo 18 usa hash routing)
        var currentHash = window.location.hash.toLowerCase();
        var currentUrl = window.location.href.toLowerCase();
        console.log('URL completa:', window.location.href);
        console.log('Hash:', currentHash);
        
        // Analisar parâmetros no hash
        if (currentHash.includes('model=res.partner')) {
            // Verificar action_id ou view_type
            if (currentHash.includes('action=') || currentHash.includes('action_id=')) {
                var actionMatch = currentHash.match(/action[_id]*=(\d+)/);
                if (actionMatch) {
                    console.log('Action ID detectado:', actionMatch[1]);
                }
            }
            
            // Verificar contexto no hash
            if (currentHash.includes('customer') || currentHash.includes('customer_rank')) {
                isCustomer = true;
                console.log('✅ Detectado como CLIENTE pelo hash (customer context)');
            } else if (currentHash.includes('supplier') || currentHash.includes('supplier_rank')) {
                isSupplier = true;
                console.log('✅ Detectado como FORNECEDOR pelo hash (supplier context)');
            }
        }
        
        // 1. VERIFICAR URL DA PÁGINA
        if (!isCustomer && !isSupplier) {
            console.log('URL atual:', currentUrl);
            
            if (currentUrl.includes('customer') || 
                currentUrl.includes('cliente') ||
                currentUrl.includes('invoice')) {
                isCustomer = true;
                console.log('✅ Detectado como CLIENTE pela URL');
            } else if (currentUrl.includes('vendor') || 
                       currentUrl.includes('supplier') || 
                       currentUrl.includes('fornecedor') ||
                       currentUrl.includes('bill')) {
                isSupplier = true;
                console.log('✅ Detectado como FORNECEDOR pela URL');
            }
        }
        
        // 2. VERIFICAR BREADCRUMB (caminho de navegação)
        if (!isCustomer && !isSupplier) {
            var breadcrumb = document.querySelector('.o_breadcrumb');
            if (breadcrumb) {
                var breadcrumbText = breadcrumb.textContent.toLowerCase();
                console.log('Breadcrumb:', breadcrumbText);
                
                if (breadcrumbText.includes('customer') || 
                    breadcrumbText.includes('cliente') ||
                    breadcrumbText.includes('receivable')) {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo breadcrumb');
                } else if (breadcrumbText.includes('vendor') || 
                           breadcrumbText.includes('supplier') || 
                           breadcrumbText.includes('fornecedor') ||
                           breadcrumbText.includes('payable')) {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo breadcrumb');
                }
            }
        }
        
        // 3. VERIFICAR TÍTULO DA PÁGINA/MODAL
        if (!isCustomer && !isSupplier) {
            var titles = document.querySelectorAll('h1, .modal-title, .o_form_title, .o_control_panel_title');
            titles.forEach(function(title) {
                var titleText = title.textContent.toLowerCase();
                if (titleText.includes('customer') || 
                    titleText.includes('cliente') ||
                    titleText.includes('clientes')) {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo título:', title.textContent);
                } else if (titleText.includes('vendor') || 
                           titleText.includes('supplier') || 
                           titleText.includes('fornecedor') ||
                           titleText.includes('fornecedores')) {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo título:', title.textContent);
                }
            });
        }
        
        // 4. VERIFICAR CAMPOS PRÉ-SELECIONADOS OU OCULTOS
        if (!isCustomer && !isSupplier) {
            // Verificar se há checkboxes marcados
            var customerCheckbox = document.querySelector('input[name="is_customer"]:checked, input[name="customer"]:checked');
            var supplierCheckbox = document.querySelector('input[name="is_supplier"]:checked, input[name="supplier"]:checked, input[name="vendor"]:checked');
            
            if (customerCheckbox) {
                isCustomer = true;
                console.log('✅ Detectado como CLIENTE por checkbox');
            }
            if (supplierCheckbox) {
                isSupplier = true;
                console.log('✅ Detectado como FORNECEDOR por checkbox');
            }
        }
        
        // 5. VERIFICAR CONTEXTO DA IMPORTAÇÃO PELO MODELO
        if (!isCustomer && !isSupplier) {
            // Procurar por indicadores no DOM que mostram o contexto
            var importContext = document.querySelector('.o_import_model');
            if (importContext) {
                var contextText = importContext.textContent.toLowerCase();
                console.log('Contexto de importação:', contextText);
            }
            
            // Verificar se tem campo customer_rank ou supplier_rank na lista de campos
            var fieldOptions = document.querySelectorAll('option');
            var hasCustomerRank = false;
            var hasSupplierRank = false;
            
            fieldOptions.forEach(function(option) {
                var optionValue = option.value || '';
                var optionText = option.textContent || '';
                
                if (optionValue.includes('customer_rank') || optionText.includes('Customer Rank')) {
                    hasCustomerRank = true;
                }
                if (optionValue.includes('supplier_rank') || optionText.includes('Supplier Rank')) {
                    hasSupplierRank = true;
                }
            });
            
            // Se tem customer_rank mas não supplier_rank, provavelmente é importação de clientes
            if (hasCustomerRank && !hasSupplierRank) {
                isCustomer = true;
                console.log('✅ Detectado como CLIENTE pela presença de customer_rank');
            } else if (hasSupplierRank && !hasCustomerRank) {
                isSupplier = true;
                console.log('✅ Detectado como FORNECEDOR pela presença de supplier_rank');
            }
        }
        
        // 6. VERIFICAR SE ESTÁ NA SEÇÃO DE CONTABILIDADE (Odoo 18 específico)
        if (!isCustomer && !isSupplier) {
            // Verificar menu ativo
            var activeMenu = document.querySelector('.o_menu_item.active, .o_menu_item.o_active, .o-dropdown-item.active');
            if (activeMenu) {
                var menuText = activeMenu.textContent.toLowerCase();
                console.log('Menu ativo:', menuText);
                
                if (menuText.includes('customer') || menuText.includes('cliente')) {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo menu ativo');
                } else if (menuText.includes('vendor') || menuText.includes('supplier') || menuText.includes('fornecedor')) {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo menu ativo');
                }
            }
            
            // Verificar o Control Panel do Odoo 18
            var controlPanel = document.querySelector('.o_control_panel');
            if (controlPanel) {
                var controlPanelText = controlPanel.textContent.toLowerCase();
                console.log('Control Panel:', controlPanelText);
                
                if (controlPanelText.includes('customer') || controlPanelText.includes('cliente')) {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo Control Panel');
                } else if (controlPanelText.includes('vendor') || controlPanelText.includes('supplier') || controlPanelText.includes('fornecedor')) {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo Control Panel');
                }
            }
            
            // Verificar o nome da view atual
            var viewTitle = document.querySelector('.o_view_controller_title h1, .o_form_view_title');
            if (viewTitle) {
                var viewText = viewTitle.textContent.toLowerCase();
                console.log('View Title:', viewText);
                
                if (viewText.includes('customer') || viewText.includes('cliente')) {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo título da view');
                } else if (viewText.includes('vendor') || viewText.includes('supplier') || viewText.includes('fornecedor')) {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo título da view');
                }
            }
        }
        
        // 7. VERIFICAR CONTEXTO NA MODAL DE IMPORTAÇÃO
        if (!isCustomer && !isSupplier) {
            // Verificar se existe uma modal de importação aberta
            var importModal = document.querySelector('.o_dialog_import, .modal-content');
            if (importModal) {
                // Verificar o contexto da modal
                var modalText = importModal.textContent.toLowerCase();
                console.log('Modal de importação detectada');
                
                // Verificar também os data attributes
                var dataModel = importModal.getAttribute('data-model');
                var dataContext = importModal.getAttribute('data-context');
                
                if (dataModel) console.log('Data Model:', dataModel);
                if (dataContext) console.log('Data Context:', dataContext);
            }
            
            // Verificar se há algum indicador de contexto no sessionStorage ou localStorage
            try {
                var odooContext = sessionStorage.getItem('odoo_context') || localStorage.getItem('odoo_context');
                if (odooContext) {
                    console.log('Contexto Odoo armazenado:', odooContext);
                    if (odooContext.includes('customer')) {
                        isCustomer = true;
                        console.log('✅ Detectado como CLIENTE pelo contexto armazenado');
                    } else if (odooContext.includes('supplier')) {
                        isSupplier = true;
                        console.log('✅ Detectado como FORNECEDOR pelo contexto armazenado');
                    }
                }
            } catch(e) {
                // Ignorar erros de acesso ao storage
            }
        }
        
        // 8. VERIFICAR ACTION CONTEXT NO ODOO
        if (!isCustomer && !isSupplier) {
            // Tentar acessar o contexto global do Odoo se disponível
            if (window.odoo && window.odoo.context) {
                console.log('Contexto Odoo global:', window.odoo.context);
            }
            
            // Verificar se há indicadores no DOM sobre o tipo de parceiro
            var partnerTypeIndicator = document.querySelector('[data-partner-type], [data-customer], [data-supplier]');
            if (partnerTypeIndicator) {
                if (partnerTypeIndicator.hasAttribute('data-customer') || 
                    partnerTypeIndicator.getAttribute('data-partner-type') === 'customer') {
                    isCustomer = true;
                    console.log('✅ Detectado como CLIENTE pelo indicador de tipo');
                } else if (partnerTypeIndicator.hasAttribute('data-supplier') || 
                           partnerTypeIndicator.getAttribute('data-partner-type') === 'supplier') {
                    isSupplier = true;
                    console.log('✅ Detectado como FORNECEDOR pelo indicador de tipo');
                }
            }
        }
        
        // 9. ÚLTIMO RECURSO: Verificar se estamos no módulo de contabilidade
        if (!isCustomer && !isSupplier) {
            // Verificar especificamente se o breadcrumb ou título menciona "Customers"
            var pageElements = document.querySelectorAll('*');
            for (var i = 0; i < pageElements.length; i++) {
                var elem = pageElements[i];
                // Procurar por "Customers" exato (não "Customer" genérico)
                if (elem.textContent === 'Customers' || elem.textContent === 'Clientes') {
                    console.log('✅ Encontrado texto exato "Customers" no elemento:', elem.tagName);
                    isCustomer = true;
                    break;
                } else if (elem.textContent === 'Vendors' || elem.textContent === 'Suppliers' || elem.textContent === 'Fornecedores') {
                    console.log('✅ Encontrado texto exato de fornecedores no elemento:', elem.tagName);
                    isSupplier = true;
                    break;
                }
            }
        }
        
        console.log('📊 RESULTADO FINAL - Cliente:', isCustomer, 'Fornecedor:', isSupplier);
        return { isCustomer: isCustomer, isSupplier: isSupplier };
    }
    
    // Função para adicionar numeração na tabela de preview
    function addNumberingToPreview(type, startNumber) {
        console.log('🔢 Adicionando numeração tipo:', type, 'começando em:', startNumber);
        
        // Validar startNumber
        if (!startNumber || isNaN(startNumber)) {
            console.warn('⚠️ Número inicial inválido, usando 1');
            startNumber = 1;
        }
        
        // Aguardar um pouco para garantir que a tabela seja renderizada
        setTimeout(function() {
            // Tentar diferentes seletores para encontrar a tabela de preview no Odoo 18
            var previewTable = document.querySelector(
                '.o_import_preview table, ' +
                '.o_list_table, ' +
                '.o_data_table, ' +
                '.table, ' +
                'table.o_list_view, ' +
                '.o_import_data_preview table, ' +
                '.o_dialog_import table'
            );
            
            if (!previewTable) {
                console.log('🔍 Procurando tabela de preview em toda a página...');
                // Procurar qualquer tabela na modal de importação
                var importModal = document.querySelector('.o_dialog_import, .modal-content, .o_dialog');
                if (importModal) {
                    previewTable = importModal.querySelector('table');
                }
            }
            
            if (!previewTable) {
                console.warn('⚠️ Tabela de preview não encontrada - tentando método alternativo');
                // Método alternativo: adicionar informação diretamente na página
                addNumberingInfo(type, startNumber);
                return;
            }
            
            console.log('✅ Tabela encontrada:', previewTable.className);
        
        // Adicionar coluna de numeração no header
        var headerRow = previewTable.querySelector('thead tr');
        if (headerRow && !headerRow.querySelector('.accg_numbering_header')) {
            var th = document.createElement('th');
            th.className = 'accg_numbering_header';
            th.style.backgroundColor = '#f0f0f0';
            th.style.fontWeight = 'bold';
            th.innerHTML = type === 'customer' ? '📋 Nº Cliente' : '📦 Nº Fornecedor';
            headerRow.insertBefore(th, headerRow.firstChild);
        }
        
            // Adicionar numeração em cada linha
            var dataRows = previewTable.querySelectorAll('tbody tr');
            var currentNumber = startNumber;
            
            dataRows.forEach(function(row, index) {
                if (!row.querySelector('.accg_numbering_cell')) {
                    var td = document.createElement('td');
                    td.className = 'accg_numbering_cell';
                    td.style.backgroundColor = '#e8f5e9';
                    td.style.fontWeight = 'bold';
                    td.style.textAlign = 'center';
                    td.innerHTML = currentNumber;
                    row.insertBefore(td, row.firstChild);
                    
                    // Incrementar para próxima linha
                    currentNumber++;
                }
            });
            
            console.log('✅ Numeração adicionada para', dataRows.length, 'registros');
            return currentNumber - 1; // Retornar último número usado
        }, 500); // Aguardar 500ms para garantir que a tabela seja renderizada
    }
    
    // Função alternativa para adicionar informação de numeração
    function addNumberingInfo(type, startNumber) {
        console.log('📝 Adicionando informação de numeração alternativa');
        
        // Criar div informativa
        var infoDiv = document.createElement('div');
        infoDiv.id = 'accg_numbering_info';
        infoDiv.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2196F3;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 9999;
            min-width: 250px;
        `;
        
        infoDiv.innerHTML = `
            <strong>🔢 Numeração Automática Ativa</strong><br>
            Tipo: ${type === 'customer' ? 'Cliente' : 'Fornecedor'}<br>
            Próximo número: ${startNumber}<br>
            <small>Os registros serão numerados automaticamente</small>
        `;
        
        // Remover div anterior se existir
        var existingDiv = document.getElementById('accg_numbering_info');
        if (existingDiv) {
            existingDiv.remove();
        }
        
        document.body.appendChild(infoDiv);
        
        // Remover após 10 segundos
        setTimeout(function() {
            infoDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                infoDiv.remove();
            }, 300);
        }, 10000);
    }
    
    // Função para processar importação com numeração
    function processImportWithNumbering() {
        if (isProcessing) {
            console.log('⏳ Já processando, aguarde...');
            return;
        }
        
        isProcessing = true;
        console.log('🚀 Processando importação com numeração...');
        
        // Aguardar um momento para garantir que o DOM está completo
        setTimeout(function() {
            processImportWithNumberingDelayed();
        }, 100);
    }
    
    function processImportWithNumberingDelayed() {
        // Detectar tipo de importação
        var importType = detectImportType();
        
        // VERIFICAÇÃO ADICIONAL: Perguntar ao usuário se não detectou automaticamente
        if (!importType.isCustomer && !importType.isSupplier) {
            console.log('⚠️ Tipo não detectado automaticamente. Perguntando ao usuário...');
            
            // Criar diálogo de confirmação
            var userChoice = confirm(
                '📋 TIPO DE IMPORTAÇÃO NÃO DETECTADO\n\n' +
                'O sistema não conseguiu detectar automaticamente o tipo de importação.\n\n' +
                'Esta é uma importação de CLIENTES?\n\n' +
                '✅ OK = Clientes\n' +
                '❌ Cancelar = Fornecedores\n\n' +
                'Ou feche esta mensagem para importar sem numeração automática.'
            );
            
            if (userChoice === true) {
                importType.isCustomer = true;
                console.log('👤 Usuário confirmou: CLIENTE');
            } else if (userChoice === false) {
                importType.isSupplier = true;
                console.log('🏢 Usuário confirmou: FORNECEDOR');
            } else {
                console.log('ℹ️ Usuário cancelou - continuando sem numeração...');
                isProcessing = false;
                return;
            }
        }
        
        // Determinar qual tipo de numeração usar
        var numberType = importType.isCustomer ? 'customer' : 'supplier';
        
        // Obter próximo número disponível
        getNextNumber(numberType).then(function(nextNumber) {
            // Armazenar dados de numeração no sessionStorage para interceptação
            var numberingData = {
                type: numberType,
                startNumber: nextNumber,
                fieldName: numberType === 'customer' ? 'accg_nr_order_customer' : 'accg_nr_order_supplier'
            };
            sessionStorage.setItem('accg_numbering_data', JSON.stringify(numberingData));
            console.log('💾 Dados de numeração armazenados:', numberingData);
            
            // Adicionar numeração visual na tabela
            var lastUsed = addNumberingToPreview(numberType, nextNumber);
            
            // Adicionar campo oculto para mapear a numeração
            addHiddenNumberingField(numberType, nextNumber);
            
            // Mostrar notificação ao usuário
            showNotification(
                '✅ Numeração Automática Aplicada',
                'Tipo: ' + (importType.isCustomer ? 'Cliente' : 'Fornecedor') + '\n' +
                'Próximo número: ' + nextNumber
            );
            
            isProcessing = false;
        });
    }
    
    // Função para adicionar campo oculto com numeração
    function addHiddenNumberingField(type, startNumber) {
        // Verificar se já existe
        if (document.querySelector('#accg_numbering_data')) {
            return;
        }
        
        // Criar campo oculto com os dados de numeração
        var hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.id = 'accg_numbering_data';
        hiddenField.name = 'accg_numbering_data';
        hiddenField.value = JSON.stringify({
            type: type,
            startNumber: startNumber,
            fieldName: type === 'customer' ? 'accg_nr_order_customer' : 'accg_nr_order_supplier'
        });
        
        // Adicionar ao formulário
        var form = document.querySelector('form') || document.body;
        form.appendChild(hiddenField);
        
        console.log('📝 Campo de numeração adicionado:', hiddenField.value);
    }
    
    // Função para mostrar notificação
    function showNotification(title, message) {
        // Criar div de notificação
        var notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        
        notification.innerHTML = `
            <strong style="display: block; margin-bottom: 5px;">${title}</strong>
            <span style="white-space: pre-line;">${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        // Remover após 5 segundos
        setTimeout(function() {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                notification.remove();
            }, 300);
        }, 5000);
    }
    
    // NOTA: A interceptação de fetch foi removida pois causava conflitos com o Odoo
    // O sistema agora funciona assim:
    // 1. Detecta o tipo de importação (cliente/fornecedor)
    // 2. Obtém o próximo número da API
    // 3. Mostra visualmente a numeração que será aplicada
    // 4. Armazena os dados no sessionStorage e campo oculto
    // 5. O backend Python aplicará a numeração ao processar a importação
    
    // Função para adicionar o interceptador de cliques
    function addInterceptor() {
        document.body.addEventListener('click', function(event) {
            var element = event.target;
            
            // Verificar se é um botão ou está dentro de um botão
            while (element && element !== document.body) {
                if (element.tagName === 'BUTTON') {
                    var buttonText = element.textContent || element.innerText || '';
                    
                    // Verificar se contém "Import" ou "Importar"
                    if (buttonText.match(/import/i)) {
                        console.log("🚀 Botão de importação clicado!");
                        
                        // Código de interceptação removido para evitar conflitos
                        
                        // Capturar contexto imediato antes de processar
                        console.log("📍 Contexto no momento do clique:");
                        console.log("  - URL:", window.location.href);
                        console.log("  - Hash:", window.location.hash);
                        console.log("  - Título da página:", document.title);
                        
                        // Verificar contexto próximo ao botão
                        var parentContext = element;
                        for (var i = 0; i < 10; i++) {
                            parentContext = parentContext.parentElement;
                            if (!parentContext) break;
                            
                            var contextText = parentContext.textContent || '';
                            if (contextText.includes('Customer') || contextText.includes('Cliente')) {
                                console.log("  ✅ Contexto de CLIENTE detectado próximo ao botão");
                                // Armazenar no sessionStorage para uso posterior
                                sessionStorage.setItem('import_context_type', 'customer');
                                break;
                            } else if (contextText.includes('Vendor') || contextText.includes('Supplier') || contextText.includes('Fornecedor')) {
                                console.log("  ✅ Contexto de FORNECEDOR detectado próximo ao botão");
                                sessionStorage.setItem('import_context_type', 'supplier');
                                break;
                            }
                        }
                        
                        // Processar numeração antes da importação
                        processImportWithNumbering();
                        
                        // Pequeno delay para garantir que a numeração foi aplicada
                        setTimeout(function() {
                            console.log("✅ Continuando com importação...");
                        }, 100);
                        
                        break;
                    }
                }
                element = element.parentElement;
            }
        });
        
        console.log("✅ Interceptador adicionado com sucesso!");
    }
    
    // CSS para animações
    var style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    // Aguardar o DOM carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addInterceptor);
    } else {
        // DOM já carregado
        addInterceptor();
    }
    
    // Adicionar botão de teste (temporário para debug)
    setTimeout(function() {
        if (window.location.href.includes('/odoo/customers/import')) {
            var testButton = document.createElement('button');
            testButton.innerHTML = '🧪 Testar API Numeração';
            testButton.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: #ff5722;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                z-index: 99999;
            `;
            testButton.onclick = function() {
                console.log('🧪 Testando API manualmente...');
                getNextNumber('customer').then(function(result) {
                    alert('Próximo número cliente: ' + result);
                });
            };
            document.body.appendChild(testButton);
        }
    }, 2000);
    
    console.log("✨ Import Numerator carregado com sucesso!");
})();