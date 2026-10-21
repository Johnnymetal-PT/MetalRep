# MMConnect

Addon Odoo 18 pensado para suportar a migração funcional do legado TimeConnect/MMConnect.

## Âmbito incluído

- estrutura RH e parametrização base;
- assiduidade, processamento, bancos e serviço externo;
- escalas, distribuição de tempo e cockpit supervisor;
- despesas, visitas, salas e reservas de viaturas;
- dispositivos, biometrias, acessos, georreferência e LPR;
- RGPD, importações e verticais base de tarefas/agro/waste/obras.

## Instalação

1. Adicionar esta pasta ao `addons_path`.
2. Atualizar a lista de apps.
3. Instalar `MMConnect`.

## Nota

Este addon fornece a fundação funcional e técnica da migração. As integrações concretas com hardware, protocolos proprietários e regras profundas de cálculo devem ser ajustadas contra uma base real e UAT funcional.

## Troubleshooting

Este módulo não depende de `approvals`. Se a instalação falhar durante a carga de `enterprise/approvals/security/approval_security.xml`, o problema está no ambiente Odoo e não no `mmconnect`.
