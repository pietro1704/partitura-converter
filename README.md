# Partitura Converter

App local para converter partituras em PDF/JPG/PNG para formatos editáveis.

Fluxo:

- Entrada: PDF, JPG, PNG, um ou vários arquivos
- OMR: Audiveris CLI
- Saída: MusicXML `.mxl`/`.musicxml`
- Edição final: MuseScore Studio, Guitar Pro ou Encore via importação

## Limitação importante

Conversão de imagem/PDF para partitura editável depende de OMR e pode exigir revisão manual. Manuscritos, scans tortos ou imagens ruins tendem a falhar.

## Requisitos

- Python 3.11+
- Java 17+
- Audiveris CLI para conversão real

## Rodar com mise

```bash
cd ~/Developer/partitura-converter
mise trust
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mise run web
```

Abra:

```text
http://127.0.0.1:8000
```

## Testes

```bash
source .venv/bin/activate
mise run test
```

## Audiveris

Checar:

```bash
./scripts/check-audiveris.sh
```

Se o executável não se chamar `audiveris`, rode assim:

```bash
AUDIVERIS_CMD=/caminho/para/audiveris mise run web
```

Downloads:

```text
https://github.com/Audiveris/audiveris/releases
```

## Formatos-alvo

- MuseScore Studio: gratuito; melhor destino para revisar MusicXML de piano e guitarra.
- Guitar Pro: importe MusicXML e revise tablatura/digitação.
- Encore: importe MusicXML quando suportado; MIDI é fallback menos fiel.

## API

```text
GET  /api/health
POST /api/convert        file=<PDF/JPG/PNG>
POST /api/convert/batch  files=<PDF/JPG/PNG>...
```
