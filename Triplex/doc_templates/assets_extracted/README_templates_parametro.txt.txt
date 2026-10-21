Scripts para gerar templates Parametro Global
=============================================

Ficheiros incluidos:
- create_parametro_powerpoint_template.py
- create_parametro_word_template.py

Dependencias:
    pip install python-pptx python-docx pillow

PowerPoint:
    python create_parametro_powerpoint_template.py --logo logo_preto.webp --out Template_Parametro_PowerPoint_Completo.pptx --potx Template_Parametro_PowerPoint_Completo.potx

Word:
    python create_parametro_word_template.py --logo logo_preto.webp --out Template_Parametro_Word_Completo.docx --dotx Template_Parametro_Word_Completo.dotx

Nota:
- Coloca o ficheiro do logotipo preto na mesma pasta dos scripts, com o nome logo_preto.webp, ou indica outro caminho no parametro --logo.
- O .potx e .dotx sao criados como copia do ficheiro gerado, para uso como base/template editavel.
