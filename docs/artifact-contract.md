# Artifact contract

Contract 4 defines the shared HTML base: appearance, contextual review, typography, sound, reading navigation and stable document metadata. Use the generator for new work rather than copying a historical example. The contract preserves dotted, fading frames on wide figures and a consistent reader dock.

## Generate

```bash
python3 scripts/create_artifact.py --content /path/content.html --title 'Operational review' --document-id operations-review --theme linear --mode light --typography sobrio --output /path/review.html
python3 scripts/validate_artifact.py /path/review.html
```

Use `--help` for chapter input and supported options. Titles and IDs must be escaped; each heading/section target must be unique. The same logical document retains its ID across title changes and revisions. New documents get new IDs. Do not fabricate session or device metadata.

## Project and format selection

Read [project identity](project-identity.md) for `.margen.json`, custom company logos and explicit CLI precedence. [Document formats](document-formats.md) covers English chapter configuration and presentation mode. Existing Spanish configuration keys remain supported.

## Structure

The generator embeds complete fonts, CSS and required modules. Wide `.ancho` or `.amplio` figures are siblings of text sections inside `.hoja` or `.pagina`; nesting them in a narrow paragraph column breaks their width. Multipage documents use a grid on each `.pagina`, not a competing grid on the outer wrapper. Chapter navigation is page navigation; local content tabs use tab semantics.

Custom text wrappers use `.prosa`; intentional custom layouts may opt out with `data-ritmo="propio"`. Plain article wrappers directly inside the page also preserve the wide-figure grid. Run `validate_artifact.py --strict-composition FILE` to reject custom prose wrappers without a known spacing contract.

The base includes one appearance menu and one review surface. The hosted adapter negotiates permissions without passing credentials into artifact HTML. Theme and typography preferences are reader-specific; published source remains immutable. Preserve existing metadata keys such as `nota-documento` and runtime globals for compatibility.

## Validation

The validator checks required modules, recorded hashes, IDs, dependencies, metadata, theme settings and contract structure. It cannot prove visual quality, human-perceived sound, keyboard ergonomics or WebGL behavior. Also inspect desktop, 320/390 px, light/dark modes, reduced motion and fallback states in a browser. Do not hide document overflow to pass a layout check.

Source HTML and generated assets must agree. Rebuild after runtime or recipe changes. A historical artifact is not automatically upgraded by updating an agent's skill; regenerate and publish a new revision with the same ID. The portal may provide current reader chrome without altering stored source versions.

## Publication

Validate locally, upload a draft, review it, then promote using the expected current version. Keep permissions and audience unchanged unless explicitly requested. New artifacts are private by default. See [portal operations](portal-operations.md) and [the unified workspace](unified-workspace.md).
