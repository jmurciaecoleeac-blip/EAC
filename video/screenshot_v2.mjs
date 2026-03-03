import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
import {fileURLToPath} from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BROWSER_EXECUTABLE = '/root/.cache/ms-playwright/chromium_headless_shell-1194/chrome-linux/headless_shell';

const bundled = await bundle({
	entryPoint: path.join(__dirname, 'src/index.ts'),
	webpackOverride: (config) => config,
});

const composition = await selectComposition({
	serveUrl: bundled,
	id: 'MyComp',
	browserExecutable: BROWSER_EXECUTABLE,
});

// Frames clés : début animation / mi-parcours / état final
for (const frame of [35, 90, 155, 260]) {
	await renderStill({
		composition,
		serveUrl: bundled,
		output: path.join(__dirname, `out/preview_v2_f${frame}.png`),
		frame,
		browserExecutable: BROWSER_EXECUTABLE,
	});
	console.log(`Frame ${frame} capturée`);
}
