---
name: arquiteto
description: >-
  Constrói simuladores 3D interativos e desmontáveis de máquinas reais, edifícios
  paramétricos, casas/apartamentos/vilas 3D fotorrealistas no Blender a partir de
  rascunhos (sketches), plantas baixas ou imagens de referência (pipeline Blueprint
  peça por peça com vídeo de montagem e áudio -14 LUFS), produtos para impressão 3D
  e cenas 3D híbridas (página HTML offline com Three.js/GSAP, scripts Python para
  Blender/CAD ou integração com motores de jogo), combinando elvarofficial/teardown,
  Nyxera0x/blueprint e a metodologia de produção 3D do Kimi. Use sempre que o usuário
  pedir um "simulador 3D", "teardown", "blueprint", "visão explodida", "corte/cutaway",
  "como funciona uma máquina", "projeto arquitetônico 3D", "transformar planta ou
  rascunho em casa 3D", "vídeo de construção 3D", "modelo para impressão 3D (STL)",
  "site 3D interativo" ou invocar a habilidade "arquiteto".
---

# Arquiteto (`arquiteto` — Teardown 3D + Metodologia Kimi 3D)

Uma máquina, um edifício ou um produto inteiro ganhando vida em 3D. O visitante vê o sistema funcionando no centro da tela, acompanha os números reais nos painéis ao redor, clica em um botão para abrir em corte (*cutaway* / visão explodida) exatamente a peça que realiza o trabalho e, quando solta o mouse, a página conduz um tour guiado sozinha. O mesmo código também gera modelos paramétricos no Blender/CAD, exporta peças prontas para impressão 3D (`.stl`) ou grava um filme frame a frame a 60 fps com trilha sonora procedural sincronizada.

- **`SKILL_DIR`**: `C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto`
- Builds HTML e renderizações vão para `./teardown-out` da pasta de onde o comando é executado.
- Documentação detalhada para consulta sob demanda:
  - [Design System de UI, Tipografia e Navegação 3D Moderna (Three.js)](./references/ui-navegacao-moderna.md)
  - [Pipeline Profissional de Texturas PBR de 12 Etapas (Blender + Three.js)](./references/materiais-pbr-iluminacao.md)
  - [Metodologia Kimi 3D: Fluxos, Ferramentas e 5 Práticas](./references/kimi-3d-workflows.md)
  - [Referência Técnica do Kit Teardown (`teardown-kit`)](./references/teardown-kit-reference.md)

---

## 1. Fluxo de Trabalho em 5 Etapas (Teardown + Kimi 3D)

Sempre que iniciar ou evoluir um projeto 3D com a habilidade **Arquiteto**, siga esta sequência disciplinada:

### Etapa 1: Referência Visual & Briefing Técnico de Produção 3D
1. **Parta de uma referência real, nunca da imaginação**:
   - Solicite ou utilize foto, desenho de corte de manual, planta arquitetônica ou vídeo de referência.
   - Se o usuário ainda não tiver uma imagem de referência, ajude-o a definir a composição (silhueta limpa, fundo simples, proporções claras) e ofereça gerar uma imagem conceitual antes de iniciar a modelagem 3D.
2. **Extraia o Briefing Técnico de Produção 3D**:
   - Antes de escrever código 3D, traduza a ideia/referência em um **Briefing Técnico**:
     - **Dimensões e Unidades Reais**: Diâmetro, curso, contagem de dentes e módulo, comprimentos de elos, pé-direito, espessura de parede ou cavidades de componentes eletrônicos (em `mm` ou `m`).
     - **Abordagem de Modelagem Dual**:
       - *Paramétrica / Código* (**Three.js**, **Blender Python**, **CadQuery/FreeCAD**): Para máquinas, arquitetura, mobiliário, terrenos em curvas de nível e peças de precisão.
       - *Malha / Difusão 3D* (**Tripo 3D**, **Meshy**, **Hyper3D**, **MetaHuman** ou `.glb` existentes): Para personagens, animais, estátuas, dragões e esculturas orgânicas.
     - **Materiais PBR Explícitos**: Substitua termos vagos (*"moderno e brilhante"*) por especificações concretas (*"carcaça branca fosca roughness 0.65, articulações em alumínio anodizado cinza-escuro roughness 0.45 / envMapIntensity 0.5, visor emissivo azul intensidade 0.8"*).
     - **Premissas sobre Partes Ocultas**: Liste explicitamente qualquer suposição feita sobre regiões obstruídas na referência.

### Etapa 2: Blockout (Grey-Box) e Validação Espacial em 3 Vistas
Para cenas complexas, edifícios, cidades em miniatura ou máquinas com vários subconjuntos:
1. **Construa o Blockout Primeiro**: Posicione volumes primitivos (caixas, cilindros, gabaritos de curso) com as dimensões reais para validar escala, conexões de piso/escadas/engrenagens e ausência de colisões.
2. **Verifique 3 Vistas Fundamentais antes de detalhar**:
   - **Vista Superior / Planta (`Top-Down / Plan View`)**: Alinhamento de eixos, distribuição espacial e circulação.
   - **Vista Frontal / Nível da Rua (`Front / Street-Level / Elevation`)**: Assentamento no chão (nada flutuando ou atravessando o piso), alturas e proporções humanas/mecânicas.
   - **Vista 3/4 Herói / Entrada (`3/4 Hero / Entrance View`)**: Composição principal ocupando **60% a 70%** do viewport.
3. **Corrija Colisões com Números, Nunca com a Câmera**: Se uma peça atravessa outra, ajuste a cota ou o deslocamento no bloco de parâmetros (`kin.js`), jamais esconda o erro mudando o ângulo da câmera.

### Etapa 3: Construção Modular (Uma Fonte da Verdade)
Ao construir um simulador interativo ou explicador visual no padrão `teardown-kit`, divida o projeto por função (copiando a base mais próxima entre `v8-*`, `cessna-*` ou `strandbeest-*` em `$SKILL_DIR/sims/`):

| Arquivo | Papel na Arquitetura |
|---|---|
| `kin.js` / `math.js` | **A Matemática Pura.** Dimensões reais em unidades reais, **uma única entrada** (ângulo do virabrequim, curso `0..1`, velocidade do vento, hora do dia) e todas as poses e leituras de sensores como função pura dessa entrada. **Zero Three.js aqui.** |
| `engine.js` / `model.js` | **A Geometria 3D.** Peças torneadas (`LatheGeometry`), tubos, extrusões, elos instanciados (`InstancedMesh`) e malhas `.glb`. Expõe `update(input)` para posicionar peças e alternar modos de corte (*glass*, *section*, *solid*) ou explosão. |
| `stage.js` | **O Estúdio e Iluminação.** Estúdio claro (*Light studio*) com **uma única cor de destaque (accent)** na peça que realiza o trabalho. Sombras com `polygonOffset`, pós-processamento (GTAO com `clippingPlanes` sincronizados, Bloom com `emissive < 1.0`). |
| `console.js` | **O Painel de Instrumentos (1600×900) — Glass Translúcido Puro & Tipografia Editorial.** Segue obrigatoriamente [`references/ui-navegacao-moderna.md`](./references/ui-navegacao-moderna.md): fontes `Geist Serif` / `Timeless Serif` (peso `300`) + `Geist` / `Timeless Sans` (peso `300`, `line-height: 1.6`), **zero ALLCAPS** (*Sentence case* em toda a UI), vidro puro apenas com transparência e `backdrop-filter: blur(28px)` (sem preenchimentos brancos sólidos) e contornos/linhas divisórias finas de `1px` em todos os cartões, botões, métricas e callouts (`Toluca / Moldavite`). |
| `film.js` | **O Roteiro Determinístico.** `SCRIPT` de movimentos de operador e `render(t)` 100% pura (sem `Math.random()`, sem `Date`, sem estado acumulado entre frames; use `rng(seed)` de `teardown-kit/util.js`). |
| `live.js` | **A Página Interativa.** Botões, sliders táteis pontilhados, órbita/zoom, duplo-clique em zonas 3D para focar, atalhos de teclado e camadas de desempenho (`TIERS`) para GPUs integradas. Sem interação, roda o auto-tour de `film.js` com cursor virtual; qualquer clique entrega o controle ao usuário e 25 s de silêncio retomam o tour. |
| `score.py` | **O Som Procedural.** Sintetizado em Python puro (48 kHz, masterizado a −14 LUFS) lendo os tempos exatos de `timeline.json`. |

### Etapa 4: Refinamento de Materiais PBR (Método de 12 Etapas), Iluminação e Bibliotecas CC0
Siga obrigatoriamente o pipeline completo em [`references/materiais-pbr-iluminacao.md`](./references/materiais-pbr-iluminacao.md):
1. **Regra do Color Space e Alinhamento Sub-Pixel (`< 0.5 px`)**:
   - **Apenas o Albedo (`map`) usa `sRGB` (`THREE.SRGBColorSpace`)**. `Normal`, `Roughness`, `Height/Bump` e `AO` **devem** usar `Non-Color` (`THREE.NoColorSpace`), caso contrário a curva gama distorce as normais e deixa a superfície com aspecto de plástico.
   - Reconstrua o mapa de normais OpenGL (`128, 128, 255` = plano, vetores unitários normalizados) a partir do gradiente Sobel do Height Map suavizado (suavizando apenas os 12% de transição mais íngremes para evitar "cortinas" serrilhadas).
2. **Regra da Superfície Seca e Fosca ("Dry Rock & Wood, Not Soap")**:
   - Para madeira natural, pedra, ardósia e concreto: comprima o mapa de `roughness` na faixa **`0.62–1.0`** (`rough * 0.45 + 0.62`), reduza `specularIntensity` / `Specular IOR Level` para **`0.20–0.24`** e misture o `AO` no Albedo a **`55%`** (nunca `100%` preto puro).
   - Para superfícies mistas (ex.: **Rocha + Musgo**), use **Máscara Dupla**: uma máscara nítida (`sigma=2`) para separar o BSDF da rocha (`roughness 0.62–1.0, specular 0.2`) do BSDF do musgo (`roughness 1.0, sheen 0.6`) e uma máscara suave (`sigma=25`) que soma `+0.15` de almofada ao Height Map.
   - Se o metal parecer opaco ou estriar sob luz baixa: use `roughness >= 0.45` e `envMapIntensity ≈ 0.5` em grandes superfícies, ou aplique iluminação baseada em HDRI.
3. **Comparação de Iluminação**: Mantenha câmera e modelo fixos para testar quando pedido:
   - *Soft Studio Lighting* (padrão claro de alta legibilidade);
   - *Warm Side Lighting* (luz lateral quente para arquitetura e relevo);
   - *Cool Rim Light* (recorte frio para silhuetas mecânicas/metálicas).
4. **Bibliotecas e Assets Externos**:
   - Use **Poly Haven** (CC0) para HDRIs, texturas PBR (pedra, madeira, concreto, metal) e modelos realistas.
   - Use **Kenney** (CC0) para packs de assets estilizados e efeitos sonoros.
   - Use **GSAP** junto com Three.js quando o projeto pedir narrativa 3D guiada por rolagem de página (*scroll showcase*).
   - Mantenha a página HTML abaixo de **1 MB**; para `.glb` pesados, configure `build.json` com `{"external": {"heavy.glb": "light.glb"}}` ou `{"swap": ...}`.

### Etapa 5: Loop Obrigatório de Revisão Visual e Iteração Cirúrgica
Você não assiste ao vídeo em tempo real, mas **enxerga os frames**. Nunca dê um simulador, cena 3D ou vídeo como pronto sem inspecionar as imagens geradas:
1. Gere a folha de contato dos marcos da timeline (`--stills beats`) ou renders das 3 vistas (Planta, Frontal/Rua, 3/4).
2. Abra a imagem gerada com `read_file` e audite cada quadro contra o checklist:
   - **Mecanismo e Espaço**: Tudo que deve tocar toca? Zero interpenetração? Números dos painéis conferem com a pose física?
   - **Composição e Tipografia**: Ponto focal único? Margem limpa de `60 px` nas bordas? Nenhum rótulo cobrindo a peça ou cortado?
   - **Iteração Cirúrgica**: Ao corrigir um defeito, preserve explicitamente o que já está bom (*"Mantenha proporções e câmera atuais; altere apenas..."*).

---

## 2. Modelagem ao Vivo no Blender (Janela Aberta na Tela + MCP)

> **REGRA DE OURO PARA BLENDER**: Sempre que o usuário pedir qualquer modelagem, arquitetura, produto ou cena no **Blender**, você **DEVE** abrir o Blender visível na tela da máquina do usuário, iniciar o MCP do Blender e construir o projeto **ao vivo na viewport** (nunca em modo oculto `--background`).

### Passo a Passo Obrigatório para Projetos no Blender:

1. **Garantir o Blender Aberto na Tela + Servidor MCP Ativo (Porta `9876`)**:
   Execute imediatamente:
   ```powershell
   python "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto\scripts\blender_live.py" ensure
   ```
   - Se o Blender ainda não estiver aberto, esse comando abre a interface gráfica do **Blender 5.2** na tela do usuário com o hook [`start_mcp_gui.py`](./scripts/start_mcp_gui.py), que ativa o addon `blender_mcp`, inicia o servidor socket na porta `9876`, habilita o **Poly Haven** e coloca a Viewport 3D em modo **Material Preview**.
2. **Modelar em Etapas Visíveis na Tela (Live Progressive Modeling)**:
   - Use as ferramentas do MCP **`arquiteto-blender`** (`execute_blender_code`, `look`, `get_scene_info`, `search_assets`, `import_asset`, `generate_3d`) **ou** o cliente direto [`blender_live.py`](./scripts/blender_live.py):
     ```powershell
     # Executar um script Python de modelagem ao vivo na janela aberta do Blender e enquadrar a viewport:
     python "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto\scripts\blender_live.py" exec-file ./etapa1_blockout.py

     # Executar código inline ao vivo:
     python "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto\scripts\blender_live.py" exec-code "import bpy; ..."

     # Capturar screenshot da viewport ao vivo para auditoria visual:
     python "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto\scripts\blender_live.py" screenshot ./viewport_check.png
     ```
   - **Nunca envie tudo em um único bloco mudo se a cena for grande**: divida a construção em etapas claras (**Etapa 1: Limpeza e Blockout**, **Etapa 2: Geometria Principal**, **Etapa 3: Detalhes e Modificadores**, **Etapa 4: Materiais PBR / Assets Poly Haven e Iluminação**). Ao final de cada etapa, enquadre a viewport (`frame-all` / `bpy.ops.view3d.view_all`) para que o usuário veja o modelo crescendo ao vivo na tela dele.
3. **Verificação Visual Obrigatória**:
   - Use a ferramenta `look` do MCP ou o comando `screenshot` do `blender_live.py` e leia a imagem com `read_file` para validar proporções, conexões e materiais antes de concluir.

---

## 2B. Arquitetura Fotorrealista & Vídeo de Montagem (`arquiteto-blueprint`)

Quando o projeto for **transformar um rascunho/sketch à mão, uma planta baixa de folheto ou 3–4 imagens de referência em uma casa, apartamento, vila ou ambiente 3D fotorrealista no Blender** (construído peça por peça em código Python, validado contra referências e filmado se montando sozinho com som sincronizado em −14 LUFS), leia e siga a skill irmã do plugin:

- **Skill completa**: [`../arquiteto-blueprint/SKILL.md`](../arquiteto-blueprint/SKILL.md)
- **Kit Blender (`bkit.py`), 3 casas de referência (`courtyard`, `villa`, `apartment`), áudio (`sfx/`) e música (`tools/music.py`)**: `C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto-blueprint\`

## 2C. Execução 3D no Navegador — Preferência por Vercel `vgpu` (`arquiteto-vgpu`)

> **PREFERÊNCIA DE NAVEGADOR**: Sempre que o projeto 3D (simulador, cena interativa, shader, visualização ou casa/asset exportado do Blender) for **rodar no navegador**, tente usar primeiro **`vgpu` da Vercel** (`vercel-labs/vgpu`, WebGPU + WGSL tipado + `vgpu/scene` + `vgpu/three` + `vgpu/node` headless), recorrendo ao kit WebGL legado (`teardown-kit`) apenas como fallback ou quando solicitado explicitamente.

- **Skill completa**: [`../arquiteto-vgpu/SKILL.md`](../arquiteto-vgpu/SKILL.md)
- **Composição de cenas 3D**: [`../arquiteto-vgpu/scene.md`](../arquiteto-vgpu/scene.md)
- **Pipeline Blender → `vgpu` (bake, LODs, GLB e paridade visual)**: [`../arquiteto-vgpu/blender/index.md`](../arquiteto-vgpu/blender/index.md)

---

## 3. Comandos Rápidos do Kit Web (`$SKILL_DIR`)

Defina `$SKILL_DIR = "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto"`:

```powershell
# Compilar um dos 3 exemplos inclusos (v8-live, cessna-live, strandbeest-live) ou todos:
node "$SKILL_DIR/sims/build.mjs" v8-live

# Compilar uma máquina/cena criada em uma pasta própria (que importa 'teardown-kit/runtime.js'):
node "$SKILL_DIR/sims/build.mjs" ./minha-maquina

# Gerar folha de revisão dos beats da timeline (+0.3s após cada beat):
node "$SKILL_DIR/sims/capture.mjs" v8-film --size 1600x900 --dpr 1.2 --stills beats --cols 4 --out teardown-out/v8-beats.png

# Capturar um único frame em alta resolução:
node "$SKILL_DIR/sims/capture.mjs" v8-film --size 1600x900 --dpr 1.2 --still 12.5 --out teardown-out/v8-12.5.png

# Renderizar vídeo MP4 a 60 fps + sintetizar trilha sonora procedural (-14 LUFS) + muxar:
node "$SKILL_DIR/sims/capture.mjs" v8-film --size 1600x900 --dpr 1.2 --out teardown-out/v8-silent.mp4
python "$SKILL_DIR/run_sfx.py" "$SKILL_DIR/sims/v8-shared/score.py"
ffmpeg -y -i teardown-out/v8-silent.mp4 -i teardown-out/v8-score.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart teardown-out/v8.mp4
```

Para detalhes completos sobre armadilhas do Three.js no Windows/ANGLE, curvas `cubic-bezier`, geração de `.stl` para impressão 3D e integração com Blender/Unreal/Unity/Godot, leia os arquivos em [`references/`](./references/).
