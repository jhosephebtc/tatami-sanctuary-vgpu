# Arquiteto (`arquiteto`)

Uma habilidade avançada de engenharia, arquitetura e visualização 3D que une o motor de simulação interativa [**elvarofficial/teardown**](https://github.com/elvarofficial/teardown), o pipeline arquitetônico em Blender [**Nyxera0x/blueprint**](https://github.com/Nyxera0x/blueprint) e a metodologia completa de produção 3D do [**Kimi 3D Academy (How to Create Better 3D Projects with Kimi)**](https://www.kimi.ai/academy/3d-tutorial).

## O que o Arquiteto faz

1. **Blueprint Arquitetônico no Blender (`arquiteto-blueprint`)**
   - Converte um rascunho à mão, uma planta baixa de folheto imobiliário ou 3–4 imagens de referência em uma casa/apartamento/vila 3D fotorrealista escrita 100% em código Python para Blender (`kit/bkit.py`), com cada sapata, pilar, viga, tábua, tatame, shoji e telha como objeto separado.
   - Inclui 3 projetos completos de referência (`courtyard`, `villa`, `apartment`), validação visual lado a lado contra referências, otimização para GPUs de 8 GB (bevels assados + LOD de árvores Poly Haven) e filme da casa se construindo sozinha sobre o desenho original com áudio procedural e música masterizada a −14 LUFS.

2. **Simuladores 3D Interativos e Desmontáveis (`teardown-kit` + Three.js)**
   - Constrói máquinas reais, mecanismos, motores, trens de pouso e estruturas em **uma única página HTML offline** (< 1 MB, com Three.js e fontes embutidas).
   - Painéis de telemetria ao vivo, gráficos sincronizados com a física/cinemática real, modos de corte (*cutaway*, vidro, seção, raio-X), isolamento de subsistemas e tour automático com cursor (retoma o controle após 25s de inatividade).
   - Gravação frame a frame em vídeo MP4 a 60 fps (`sims/capture.mjs`) com trilha sonora procedural sincronizada em Python a −14 LUFS (`run_sfx.py`).

2. **Modelagem Dual e Roteamento de Ferramentas (Metodologia Kimi 3D)**
   - **Modelagem Paramétrica e via Código**: Para objetos definidos por dimensões, estruturas e regras (peças mecânicas, arquitetura, mobiliário, gabinetes e produtos para impressão 3D) usando **Three.js**, **Blender Python**, **CadQuery / FreeCAD / Rhino**.
   - **Modelagem de Malha Orgânica (Mesh Generation)**: Para personagens, animais, estátuas e adereços orgânicos complexos, preparando prompts e referências multi-ângulo para geradores de malha (**Tripo 3D**, **Meshy**, **Hyper3D**, **MetaHuman**) e integrando os arquivos `.glb` ao cenário paramétrico.

3. **As 5 Práticas de Produção 3D do Kimi**
   - **Referência Visual Primeiro**: Uso de fotos, diagramas de corte, silhuetas claras e cotas mecânicas (ou geração prévia de imagem conceitual).
   - **Briefing Técnico de Produção 3D**: Tradução da referência visual em especificações acionáveis (formas, proporções, materiais PBR explícitos, iluminação e premissas sobre partes ocultas).
   - **Blockout (Grey-Box) → Validação em 3 Vistas → Refinamento**: Construção inicial com primitivas simples e validação nas vistas *Top-Down (Planta)*, *Frontal / Nível da Rua (Elevação)* e *3/4 (Entrada/Herói)* antes de detalhar geometria, materiais PBR e luzes (Soft Studio, Warm Side, Cool Rim, Poly Haven HDRIs).
   - **Reuso de Bibliotecas CC0 e Animação**: Integração nativa com **Poly Haven** (HDRIs, texturas PBR e modelos CC0), **Kenney** (packs de assets e áudio CC0) e **GSAP + Three.js** (narrativas 3D guiadas por scroll).
   - **Empacotamento de Fluxos**: Transformação de templates de câmera, materiais, iluminação e checagens em habilidades reutilizáveis.

## Estrutura do Plugin

- `mcp_config.json`: Servidor MCP `arquiteto-blender` (`mcp-for-blender` na porta `9876`).
- `rules/AGENTS.md`: Regra sempre ativa priorizando **Vercel `vgpu` (WebGPU)** para qualquer cena/simulador 3D que rode no navegador.
- `skills/arquiteto/SKILL.md`: Instruções principais da habilidade `arquiteto` (Teardown + Kimi 3D + Blender Ao Vivo).
- `skills/arquiteto-blueprint/SKILL.md`: Pipeline completo do `Nyxera0x/blueprint` (3 casas em `houses/`, `kit/bkit.py`, `sfx/`, `tools/music.py`).
- `skills/arquiteto-vgpu/SKILL.md`: Skill oficial do **Vercel `vgpu`** (`vercel-labs/vgpu`) com `scene.md` e pipeline `blender/` para rodar cenas 3D e assets do Blender em WebGPU no navegador.
- `skills/arquiteto/scripts/blender_live.py` e `start_mcp_gui.py`: Inicializador automático da interface gráfica do Blender 5.2 na tela do usuário com o servidor MCP ativo e modelagem progressiva ao vivo.
- `skills/arquiteto/references/kimi-3d-workflows.md`: Guia detalhado dos fluxos, tabelas, exemplos passo a passo e as 5 dicas do Kimi 3D Tutorial.
- `skills/arquiteto/references/teardown-kit-reference.md`: Referência técnica completa do kit Teardown (`build.mjs`, `capture.mjs`, `run_sfx.py`, contrato `render(t)`, armadilhas de Three.js e checklist de revisão).
- `skills/arquiteto/sims/`: Kit de runtime (`sims/kit/`) e 3 simuladores completos de exemplo (`v8-*`, `cessna-*`, `strandbeest-*`).
- `skills/arquiteto/sfx/`: Sintetizador procedural de áudio em Python (48 kHz, −14 LUFS) e samples CC0.
