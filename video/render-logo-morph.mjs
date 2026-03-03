import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import path from 'path';
import {fileURLToPath} from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const BROWSER_EXECUTABLE =
	'/root/.cache/ms-playwright/chromium_headless_shell-1194/chrome-linux/headless_shell';

const bundled = await bundle({
	entryPoint: path.join(__dirname, 'src/index.ts'),
	webpackOverride: (config) => config,
});

const composition = await selectComposition({
	serveUrl: bundled,
	id: 'JPOLogoMorph',
	browserExecutable: BROWSER_EXECUTABLE,
	timeoutInMilliseconds: 120000,
});

console.log('Rendu JPO Logo Morph (450 frames, 1080×1920)…');

await renderMedia({
	composition,
	serveUrl: bundled,
	codec: 'h264',
	outputLocation: path.join(__dirname, 'out/jpo-logo-morph.mp4'),
	browserExecutable: BROWSER_EXECUTABLE,
	timeoutInMilliseconds: 120000,
});

console.log('✓ Vidéo rendue : out/jpo-logo-morph.mp4');
