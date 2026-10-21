# -*- coding: utf-8 -*-
"""Regista a conta bancaria portuguesa da empresa.

`PORQUE E' QUE ISTO E' DELICADO`
Um IBAN errado numa factura e' dinheiro a entrar na conta de outra pessoa. Por
isso o numero e' reconferido aqui por tres vias independentes antes de qualquer
escrita, e o guiao recusa-se a escrever se alguma falhar.

  1. modulo 97 (norma ISO 13616) tem de dar resto 1
  2. o codigo de banco do IBAN tem de ser 0018 e o BIC TOTAPTPL — Santander Totta
  3. o NIF impresso no documento do banco tem de ser o **da empresa na base**

`E PORQUE E' QUE EU CONSEGUI LER O NUMERO AGORA`
O PDF nao e' uma digitalizacao, como eu tinha concluido. Tem camada de texto,
mas as fontes sao subconjuntos com codificacao propria: cada glifo esta gravado
com o codigo **menos 29**, em cadeias de dois bytes. Uma extracao normal
devolve lixo, e eu li o lixo como sendo uma imagem.

  FASE=ver       o que ha' hoje
  FASE=aplicar   cria a conta (exige ESCREVER=1)
"""
import os

FASE = os.environ.get('FASE', 'ver')
ESCREVER = os.environ.get('ESCREVER') == '1'

IBAN = 'PT50001800036905960802090'
BIC = 'TOTAPTPL'
NIF_NO_DOCUMENTO = '516617770'
BANCO = 'Banco Santander Totta S.A.'


def mod97(iban):
    rot = iban[4:] + iban[:4]
    num = ''.join(str(ord(c) - 55) if c.isalpha() else c for c in rot)
    return int(num) % 97


print('')
print('=' * 72)
print('CONTA BANCARIA DA EMPRESA')
print('=' * 72)
emp = env.company
print('  empresa : %s' % emp.name)
print('  NIF     : %s' % (emp.vat or '(sem NIF)'))

print('')
print('--- contas actuais ---')
contas = env['res.partner.bank'].with_context(active_test=False).search(
    [('partner_id', '=', emp.partner_id.id)])
if not contas:
    print('  (nenhuma)')
for c in contas:
    print('  %-30s %-28s activa=%s' % (c.acc_number, c.bank_id.name or '-', c.active))

print('')
print('--- as tres conferencias ---')
falhas = []


def conferir(t, ok, det):
    print('  [%s] %-42s %s' % ('OK' if ok else '!!', t, det))
    if not ok:
        falhas.append(t)


conferir('modulo 97 da norma ISO 13616', mod97(IBAN) == 1, 'resto %d' % mod97(IBAN))
conferir('codigo de banco coerente com o BIC',
         IBAN[4:8] == '0018' and BIC == 'TOTAPTPL', '%s / %s' % (IBAN[4:8], BIC))
nif_base = (emp.vat or '').replace('PT', '').strip()
conferir('NIF do documento igual ao da empresa', nif_base == NIF_NO_DOCUMENTO,
         '%s vs %s' % (NIF_NO_DOCUMENTO, nif_base or '(vazio)'))
ja = contas.filtered(lambda c: (c.acc_number or '').replace(' ', '') == IBAN)
conferir('conta ainda nao registada', not ja,
         'nova' if not ja else 'ja existe, id=%s' % ja[0].id)

if falhas:
    print('')
    print('  PARADO: %s' % ', '.join(falhas))
elif FASE == 'aplicar':
    if not ESCREVER:
        print('')
        print('  (ensaio — ESCREVER=1 para criar)')
    else:
        banco = env['res.bank'].search([('bic', '=', BIC)], limit=1)
        if not banco:
            banco = env['res.bank'].search([('name', 'ilike', 'santander totta')], limit=1)
        if not banco:
            banco = env['res.bank'].create({'name': BANCO, 'bic': BIC})
            print('')
            print('  banco criado: %s' % banco.name)
        else:
            print('')
            print('  banco existente: %s (bic %s)' % (banco.name, banco.bic or '-'))
        nova = env['res.partner.bank'].create({
            'acc_number': IBAN,
            'partner_id': emp.partner_id.id,
            'bank_id': banco.id,
            'company_id': emp.id,
        })
        env.cr.commit()
        print('  conta criada: id=%s  %s' % (nova.id, nova.acc_number))
        print('')
        print('--- releitura ---')
        for c in env['res.partner.bank'].search([('partner_id', '=', emp.partner_id.id)]):
            print('  %-30s %-28s activa=%s' % (c.acc_number, c.bank_id.name or '-', c.active))
        print('')
        print('  Correr o evo_relatorios.py FASE=render a seguir: e ele que diz')
        print('  se a conta sai impressa no documento, e nao esta listagem.')

print('')
print('IBAN=FIM')
