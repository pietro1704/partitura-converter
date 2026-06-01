# Partitura Converter

App local para converter partituras em PDF/JPG/PNG para formatos editáveis.

Fluxo inicial:

- Entrada: PDF, JPG, PNG
- OMR: Audiveris CLI, quando instalado
- Saída: MusicXML `.mxl`/`.musicxml`
- Uso posterior: MuseScore, Guitar Pro e Encore via importação de MusicXML/MIDI

## Limitação importante

Conversão de imagem/PDF para partitura editável depende de OMR e pode exigir revisão manual. Manuscritos, scans tortos ou imagens ruins tendem a falhar.

## Requisitos

- Python 3.11+
- Java 17+
- Audiveris CLI opcional, mas necessário para conversão real

## Rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra:

```text
http://127.0.0.1:8000
```

## Testes

```bash
pytest
```

## Instalar Audiveris

Baixe em:

```text
https://github.com/Audiveris/audiveris
```

Depois garanta que o comando `audiveris` esteja no PATH.

## Formatos-alvo

- MuseScore: importar MusicXML diretamente
- Guitar Pro: importar MusicXML no Guitar Pro
- Encore: importar MusicXML/MIDI quando suportado pela versão
