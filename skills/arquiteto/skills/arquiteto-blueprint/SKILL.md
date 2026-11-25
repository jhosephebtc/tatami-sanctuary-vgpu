---
name: arquiteto-blueprint
description: >-
  Transforma uma planta baixa, um rascunho à mão (sketch) ou 3–4 imagens de referência
  em uma casa/apartamento/vila 3D fotorrealista no Blender (em código Python) e em um
  filme da construção se montando peça por peça sobre o desenho original, com som
  sincronizado em -14 LUFS. Cada sapata, pilar, viga, tábua, tatame, tira de shoji e
  painel de telhado é um objeto próprio. Use sempre que o usuário enviar ou descrever
  uma planta, rascunho, folheto imobiliário ou referências de uma casa, apartamento,
  vila ou ambiente para gerar 3D em Blender, renders fotorrealistas, walkthrough ou
  vídeo de montagem arquitetônica ("blueprint" / "arquiteto").
---

# Arquiteto Blueprint (`arquiteto-blueprint`)

Baseado em [`Nyxera0x/blueprint`](https://github.com/Nyxera0x/blueprint) e integrado ao plugin global **`arquiteto`**.

Um input, uma cena Blender inteira em código Python, um conjunto de stills validados lado a lado contra referências e um filme da casa se construindo sozinha sobre o input original. Nada é modelado manualmente e nenhum arquivo 3D fixo da casa existe: a cena é um script Python que o agente escreve, renderiza, inspeciona visualmente e corrige iterativamente.

- **`SKILL_DIR`**: `C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto-blueprint`
- **Saída de renders e frames**: `$BLUEPRINT_OUT` (padrão `./blueprint-out` no diretório atual).
- **Assets CC0 (Poly Haven)**: `$BLUEPRINT_ASSETS` (padrão `~/.blueprint/polyhaven`).
- **Executável do Blender no Windows**: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"` (ou `blender` se estiver no PATH).

## Pré-requisitos

- **Blender 4.2+** (instalado em `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; testado com Cycles em GPU NVIDIA OptiX/CUDA; 8 GB de VRAM bastam seguindo as regras de "Fit the card").
- **Python 3** (`C:\Python313\python.exe`) com `pillow` (overlay de contador HUD), `opencv-python` e `numpy` (leitura de plantas baixas).
- **ffmpeg** no PATH (ou variável `FFMPEG=/caminho/para/ffmpeg`).
- **Opcional**: `ELEVENLABS_API_KEY` (no ambiente ou `.env`) para gerar a trilha musical; sem a chave, `tools/music.py` mixa apenas os efeitos sonoros procedurais.

## Primeira execução (Assets CC0)

Cada casa baixa seus materiais e plantas CC0 do Poly Haven uma única vez em `~/.blueprint/polyhaven` (pulando o que já existir):

```powershell
python "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto-blueprint\houses\courtyard\fetch_assets.py"
```

## As 3 casas de referência incluídas

| Casa | Input | Pasta | O que demonstra |
|---|---|---|---|
| **Courtyard house** | Rascunho a caneta no papel (`sketch.png`) | `houses/courtyard/` | 14 × 14 m, pátio de 7 × 7 m com bordo vermelho, sala de tatame, engawa, telhado em anel standing-seam. O filme abre no sketch, monta 2.444 peças em argila branca com flash de cor por etapa e contador HUD; depois uma onda a partir do bordo transforma o papel em encosta e argila em cedro, washi e pedra. |
| **Cliff villa** | 4 imagens de referência | `houses/villa/` | Pavilhão em travertino sobre falésia ao pôr do sol, piscina de borda infinita em balanço. O filme chega sobre o mar, monta placas e blocos, enche a piscina, acende as luzes e entra pelo vidro aberto. |
| **Apartment** | Planta baixa de folheto imobiliário | `houses/apartment/` | Apartamento de 3 quartos com paredes vetorizadas do preenchimento da planta pela barra de escala, portas e móveis lidos em grade métrica (`grid_view.py`). Visão dollhouse seguida de walkthrough. |

Cada casa contém `build.py` (cena e stills), `film.py` (filme de montagem), `score.py` (sons de ação no relógio de `timeline.json`) e `music_plan.json` (plano de composição para ElevenLabs). Copie a casa mais próxima como ponto de partida para um novo projeto.

```powershell
$BLENDER = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$BP = "C:\Users\Administrador\.gemini\config\plugins\arquiteto\skills\arquiteto-blueprint"

& $BLENDER -b --factory-startup -P "$BP\houses\courtyard\build.py" -- tatami engawa corner --samples 192 --res 1920x1080
& $BLENDER -b --factory-startup -P "$BP\houses\courtyard\film.py" -- --res 1920x1080 --samples 64
python "$BP\houses\courtyard\hud.py" --frames blueprint-out/courtyard/film --out blueprint-out/courtyard/silent.mp4
python "$BP\tools\music.py" --film blueprint-out/courtyard/silent.mp4 --score "$BP\houses\courtyard\score.py" --plan "$BP\houses\courtyard\music_plan.json" --out blueprint-out/courtyard/final.mp4
```

`film.py` suporta retomada automática: frames já salvos no disco são pulados (remova placeholders vazios antes de retomar). Use `--stills 0,6,13` para checar momentos isolados e `--step 3 --res 480x270 --samples 6` para prévia rápida do filme inteiro.

> **Integração com Blender Ao Vivo (`arquiteto-blender`)**: Quando o usuário quiser acompanhar ou revisar a geometria interativamente na tela do Blender, abra a viewport com `blender_live.py ensure` (da skill `arquiteto`) para inspecionar o blockout e a cena. Para renderização em lote de stills Cycles de alta amostragem ou centenas de frames do `film.py`, execute via CLI com `$BLENDER -b --factory-startup`.

> **Publicação/Walkthrough no Navegador (`arquiteto-vgpu`)**: Quando o objetivo for levar a casa, ambiente ou asset do Blender para **rodar interativamente no navegador**, priorize **`vgpu` da Vercel** (WebGPU) seguindo [`../arquiteto-vgpu/SKILL.md`](../arquiteto-vgpu/SKILL.md) e o pipeline de exportação/bake em [`../arquiteto-vgpu/blender/index.md`](../arquiteto-vgpu/blender/index.md).

## Método completo para construir uma nova casa (10 etapas)

1. **Ler o input em números, nunca por "clima/sensação".**
   - *Rascunho (sketch)*: confie nas cotas/dimensões escritas acima dos pixels (modelos de imagem costumam desenhar um quadrado de 14 m com 745 px × 670 px).
   - *Planta baixa*: localize a barra de escala, trace o preenchimento das paredes (`extract_walls.py`) e leia portas/janelas manualmente sobre uma grade métrica (`grid_view.py`); detecção automática costuma colocar portas no meio dos cômodos.
   - Liste todos os cômodos (cantos em metros), espessura de paredes, largura/altura de portas e janelas, móveis e inconsistências antes de gerar geometria.
2. **Fixar o visual com 3–4 referências.**
   - Escreva prompts de imagem coerentes para as vistas principais (ex.: vista alta de canto, interior olhando para o ponto focal, detalhe de varanda/material), mantendo a mesma paleta de materiais em todas. Elas decidem cada material, luminária e almofada.
3. **Construir como um carpinteiro (cada peça é um objeto próprio).**
   - Sapatas, vigas baldrame, caibros, pilares, frechais, tesouras, painéis de telhado, tábuas de revestimento e piso, cada tatame com borda preta, cada shoji com suas ripas kumiko, vidros, móveis e pedras de jardim.
   - Marque cada peça com sua etapa (`K.STAGE[0] = "frame"`, usando `kit/bkit.py`) para que `film.py` anime a entrada por etapa e o contador HUD conte cada objeto.
   - Enderece alas repetidas por lado e coordenadas `(u, v)` em uma única função para que rincões e espigões caiam exatos nas diagonais.
4. **Renderizar stills lado a lado com as referências e corrigir divergências.**
   - Comece em baixa resolução (`960x540`, `32 samples`), abra a imagem com `read_file` junto à referência, faça uma lista objetiva de diferenças (proporções, materiais, luz, itens ausentes, peças atravessando telhado/piscina), corrija tudo e re-renderize até zerar a lista.
5. **Escolher a luz por último — e mostrar duas versões (`--look day|dusk`).**
   - Blue hour / dusk pode ficar sombrio demais; um dia claro após a chuva (sol baixo, tábuas úmidas, céu pálido, luzes internas à meia força) dá leitura aberta. Implemente `--look day|dusk` na mesma câmera.
6. **Filmar a casa se construindo sozinha sobre o input.**
   - Abra no input original: o sketch como plano texturizado na escala real (ex.: 14 × 14 m), câmera top-down com lente longa (`200 mm`) que espirala para baixo enquanto reduz a distância focal (o plano mantém o tamanho enquanto a perspectiva abre).
   - Faça as peças voarem por etapa em argila branca com flash de cor por sistema + contador HUD no canto.
   - Dispare um evento de transformação (onda de materiais saindo do ponto focal, acendimento de luzes), uma pausa lenta e o mergulho para dentro do ambiente, encerrando no enquadramento da vista de referência.
   - Salve `timeline.json` com o instante exato de cada pouso/evento.
7. **Fazer caber em GPU de 8 GB ("Fit the card").**
   - Motion blur em milhares de peças animadas estoura 8 GB de VRAM.
   - Liste malhas por contagem de polígonos e texturas por tamanho.
   - **Aplique/asse (bake) modificadores Bevel** nas malhas antes de criar keyframes (o Cycles trata malhas com modificador como deformáveis e armazena vértices por sub-step de blur).
   - Use cópias decimadas (~8×) de vegetação escaneada pesada apenas para o filme (`make_tree_lod.py` — coníferas do Poly Haven chegam a 2–7 milhões de polígonos cada), mantendo a malha completa nos stills.
8. **Sonorizar no relógio exato do filme.**
   - `score.py` lê `timeline.json` e dispara timbres coerentes com o material de cada etapa (pedra para fundação, madeira oca para pilares/vigas, papel para washi, metal fino para telhado, folhas/chuva na onda).
   - Com trilha musical (arquivo próprio via `--music` ou ElevenLabs via `--plan`), localize o crescendo (swell) da música e ajuste `--offset` para coincidir com a onda de revelação. Masterize em **−14 LUFS**.
9. **Revisar frames, nunca apenas código.**
   - Gere folhas de contato em baixa resolução a cada segundo do filme antes de disparar o render final pesado.

## Regras essenciais aprendidas na prática

- **Tone mapping**: use **Khronos PBR Neutral**. `AgX` transforma pores do sol alaranjados em bege lavado.
- **Vidro fino**: misture `Transparent BSDF` + `Glossy BSDF` por `Fresnel`, sem refração. `Smooth shading` em caixa sem bevel distorce vidros como lentes — só suavize com bevel + *harden normals*.
- **Arquivos "set" do Poly Haven** (fileira de arbustos, monte de pedras): separe em plantas individuais (`model_variants` em `bkit.py`).
- **Nó Mix no Shader Editor**: `clamp_factor` vem ligado por padrão — desative-o ao somar disco solar ou halo sobre o céu.
- **Juntas de azulejo pintadas**: duplicam visualmente quando a laje é fatiada em peças reais para o filme — remova as juntas pintadas nessa etapa.
- **Câmera nunca encara parede lisa de perto**: ao entrar por uma abertura, gire para a vista principal ainda na abertura e recue para dentro do cômodo.
- **Duração orgânica**: filmes entre 18 e 25 s (evite durações artificialmente redondas); cada casa tem seu próprio ritmo.
- **Direitos de imagem**: mantenha apenas arquivos do usuário ou CC0 em repositórios públicos (plantas de folhetos comerciais ficam apenas localmente com o usuário).
