# Regra do Plugin Arquiteto — Navegador com Vercel `vgpu` (WebGPU)

Sempre que um projeto 3D, simulador interativo, visualização, shader ou asset exportado do Blender precisar **rodar no navegador**, priorize **`vgpu` (Vercel Labs — WebGPU)** como engine/camada gráfica principal:

1. **Engine padrão no navegador**:
   - Use `vgpu` (`vgpu`, `vgpu/scene`, `@vgpu/wgsl-std`, ou o adaptador `vgpu/three` com Three.js WebGPU/TSL quando precisar do ecossistema Three.js) como primeira escolha para renderização 3D e shaders no browser.
   - Use `vgpu/node` (Dawn headless) ou `vgpu/mock` para testes automatizados e validação de shaders sem precisar de janela ativa.
   - Só recorra a WebGL legado / HTML único offline (`teardown-kit`) como fallback se o navegador/ambiente não suportar WebGPU ou se o usuário pedir explicitamente o formato legado.
2. **Fonte de verdade da API**:
   - Antes de escrever código `vgpu`, carregue a skill **`arquiteto-vgpu`** (`skills/arquiteto-vgpu/SKILL.md`), verifique a versão instalada no projeto e consulte a documentação embutida via CLI (`vgpu docs cat`, `vgpu docs find`, `vgpu docs grep`). Nunca invente APIs de memória.
   - Para composição de cenas 3D, leia `skills/arquiteto-vgpu/scene.md`.
   - Para exportar/assar (bake) assets do Blender para o navegador em `vgpu` (GLB, LODs, normais, AO, validação visual), leia `skills/arquiteto-vgpu/blender/index.md` e suas referências.
