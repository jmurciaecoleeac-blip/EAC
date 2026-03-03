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

for (const frame of [30, 110, 165, 260]) {
	await renderStill({
		composition,
		serveUrl: bundled,
		output: path.join(__dirname, `out/preview_f${frame}.png`),
		frame,
		browserExecutable: BROWSER_EXECUTABLE,
	});
	console.log(`Frame ${frame} capturée`);
}
