# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# crawler/items.py
from scrapy.item import Item, Field

class ProductDetailsItem(Item):
    Referencia = Field()
    NOME_PRODUTO = Field()
    CodMarca = Field()
    NOME_MARCA = Field()
    Cod_Gama = Field()  # Adjusted key to be valid Python identifier
    NOME_GAMA = Field()
    Cod_Familia = Field() # Adjusted key
    NOME_FAMILIA = Field()
    SUBFAMILIA = Field()
    NOME_SUBFAMILIA = Field()
    PR_LIQUIDO = Field()
    PartNr = Field()
    EAN = Field()
    Peso_kg = Field()      # Adjusted key
    Volume_dm3 = Field()   # Adjusted key
    Comprimento_mm = Field() # Adjusted key
    Largura_mm = Field()   # Adjusted key
    Altura_mm = Field()    # Adjusted key
    LinkImagem = Field()
    Caracteristicas_Resumo = Field()
    Caracteristicas_Completa = Field()
    Classe_energetica = Field()
    Link_Classe_Energetica = Field()
    Stock = Field()
    Selo_Classe_Energetica = Field()
    QtdLinear = Field()
    OutrasFotos = Field()