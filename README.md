# Achadinhos Delas

Site estatico de curadoria de ofertas Shopee para nicho feminino.

## Publicacao

O site publicado fica em:

`outputs/publicar-achadinhos-delas`

## Atualizacao automatica

O workflow `.github/workflows/update-achadinhos.yml` roda todos os dias as 21h no horario de Brasilia/Sao Paulo.

Ele usa o segredo `SHOPEE_FEED_URLS` para baixar os feeds CSV da Shopee, filtra os produtos e publica no GitHub Pages.

Configure o segredo no GitHub com os links dos feeds, um por linha.
