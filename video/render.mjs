import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
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

console.log('Rendu de la vidéo en cours...');

await renderMedia({
	composition,
	serveUrl: bundled,
	codec: 'h264',
	outputLocation: path.join(__dirname, 'out/video.mp4'),
	browserExecutable: BROWSER_EXECUTABLE,
});

console.log('Vidéo rendue avec succès : out/video.mp4');
