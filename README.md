# Beep Estoque Pro 2.0 🇧🇷

Aplicativo de controle de estoque em Python + Kivy, com interface em português do Brasil e banco de dados SQLite local.

> **Status:** projeto em desenvolvimento. Este repositório contém código-fonte; não contém APK pronto para instalar.

## Funcionalidades

- Painel com indicadores de estoque.
- Cadastro, edição, exclusão e pesquisa de produtos.
- Pesquisa por nome, descrição e código de barras.
- Controle de validade e estoque mínimo.
- Registro de entradas e saídas com histórico.
- Exportação CSV compatível com Excel.
- Exportação PDF opcional.
- Banco SQLite local para uso sem internet.
- Tela de código de barras com entrada manual e prévia de câmera em ambientes compatíveis.

## Requisitos

- Python 3.10 ou superior.
- Kivy 2.3 ou superior.

## Instalação e execução

### Windows, Linux ou macOS

1. Baixe o projeto pelo botão **Code → Download ZIP** do GitHub ou clone o repositório.
2. Abra o terminal na pasta do projeto.
3. Instale as dependências:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Inicie o aplicativo:

   ```bash
   python main.py
   ```

### Exportar PDF (opcional)

Instale o ReportLab:

```bash
python -m pip install reportlab
```

## Gerar APK para Android

A configuração inicial do Buildozer está incluída. Para compilar, normalmente é necessário Linux ou WSL2 com as dependências Android:

```bash
python -m pip install buildozer
buildozer android debug
```

A compilação Android pode exigir ajustes conforme a versão do sistema e do Buildozer. O arquivo `buildozer.spec` é uma configuração inicial, não uma garantia de compilação sem ajustes.

## Limitações conhecidas

- A leitura automática do código de barras pela câmera ainda precisa ser integrada e testada em aparelho Android.
- A sincronização com nuvem/uso online ainda não foi implementada.
- Faça backup periódico do arquivo `estoque.db`, criado localmente pelo aplicativo.
- Teste o aplicativo com dados fictícios antes de usá-lo em uma operação real.

## Estrutura do projeto

```text
beep-estoque-pro/
├── app/
│   ├── database.py
│   └── exporter.py
├── .github/
│   └── workflows/
│       └── python-check.yml
├── main.py
├── requirements.txt
├── buildozer.spec
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Contribuições

Sugestões e melhorias são bem-vindas. Consulte [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).
