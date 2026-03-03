import React from 'react';
import {
	AbsoluteFill,
	Easing,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
	Img,
} from 'remotion';
import {FONT_FAMILY} from './fonts';

// ─── PALETTE ──────────────────────────────────────────────────────────────
const RED = '#DC0D17';
const WHITE = '#FFFFFF';

// ─── CANVAS ───────────────────────────────────────────────────────────────
// 1080 × 1920, vertical (Instagram / TikTok Reels)

// ─── FRAME GEOMETRY ───────────────────────────────────────────────────────
// The "cadre" the girl holds — nearly full-width square.
const FX = 60; // frame x
const FY = 72; // frame y
const FW = 960; // frame width
const FH = 960; // frame height
const FS = 20; // frame stroke (white border thickness)

// EAC logo starting size (small square, centered inside the frame zone)
const LW = 130;
const LH = 130;
const LX = FX + FW / 2 - LW / 2; // = 470
const LY = FY + FH / 2 - LH / 2; // = 482

// Interior photo area (inside the frame border)
const PX = FX + FS;
const PY = FY + FS;
const PW = FW - FS * 2;
const PH = FH - FS * 2;

// Text section starts just below the frame
const TEXT_TOP = FY + FH + 44; // ≈ 1076

// ─── TIMING ───────────────────────────────────────────────────────────────
const T_LOGO_IN = 0; // logo rect + letters spring in
const T_MORPH_START = 38; // rect begins growing
const T_MORPH_END = 128; // rect reaches final frame size
const T_LETTERS_OUT = 82; // EAC letters fully gone
const T_PHOTO_IN = 95; // girl photo fades in
const T_PHOTO_DONE = 150; // photo fully visible
const T_TITLE = 140; // word-by-word: JOURNÉE PORTES OUVERTES
const T_EAC_LINE = 195; // "EAC" + divider
const T_DATE = 228; // "14 MARS"
const T_TIME = 258; // "10H–16H"
const T_ADDRESS = 285; // "13 RUE MIOLLIS"
const T_CTA = 318; // "RÉSERVE TA PLACE !"

// ─── HELPERS ──────────────────────────────────────────────────────────────
const ease = Easing.bezier(0.16, 1, 0.3, 1);

function fadeIn(frame: number, from: number, dur = 20) {
	return interpolate(frame, [from, from + dur], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: ease,
	});
}

function slideUp(frame: number, from: number, dur = 22, dist = 32) {
	return interpolate(frame, [from, from + dur], [dist, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: ease,
	});
}

// ─── COMPONENT ────────────────────────────────────────────────────────────
export const JPOLogoMorphComp: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// ── Logo entrance (spring) ─────────────────────────────────────────
	const logoSpring = spring({
		fps,
		frame: Math.max(0, frame - T_LOGO_IN),
		config: {damping: 18, stiffness: 220},
	});
	const logoScale = interpolate(logoSpring, [0, 1], [0.55, 1]);
	const logoOpacity = interpolate(logoSpring, [0, 0.25, 1], [0, 1, 1]);

	// ── Morph: logo rect expands to full frame ─────────────────────────
	const morphT = interpolate(frame, [T_MORPH_START, T_MORPH_END], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.16, 1, 0.3, 1),
	});

	// Rect that starts as the logo and grows to the girl's frame
	const rX = interpolate(morphT, [0, 1], [LX, FX]);
	const rY = interpolate(morphT, [0, 1], [LY, FY]);
	const rW = interpolate(morphT, [0, 1], [LW, FW]);
	const rH = interpolate(morphT, [0, 1], [LH, FH]);

	// ── Letters (E, A, C) fade out as rect grows ─────────────────────
	const lettersOpacity =
		logoOpacity *
		interpolate(frame, [T_MORPH_START, T_LETTERS_OUT], [1, 0], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		});

	// Letter positions track rect center
	const cx = rX + rW / 2;
	const letterFontSize = interpolate(morphT, [0, 1], [40, 40]); // stays 40px
	const eY = rY + rH * 0.28;
	const aY = rY + rH * 0.52;
	const cY = rY + rH * 0.75;

	// ── Photo fades in ─────────────────────────────────────────────────
	const photoOpacity = interpolate(frame, [T_PHOTO_IN, T_PHOTO_DONE], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	// ── Photo interior dims: animate to match expanding rect ──────────
	const photoX = rX + FS;
	const photoY = rY + FS;
	const photoW = rW - FS * 2;
	const photoH = rH - FS * 2;

	// ── Title words ───────────────────────────────────────────────────
	const words = ['JOURNÉE', 'PORTES', 'OUVERTES'];
	const wordOpacities = words.map((_, i) => fadeIn(frame, T_TITLE + i * 14));
	const wordTranslates = words.map((_, i) =>
		slideUp(frame, T_TITLE + i * 14),
	);

	// ── EAC label + divider ───────────────────────────────────────────
	const eacOpacity = fadeIn(frame, T_EAC_LINE);
	const dividerScale = interpolate(
		frame,
		[T_EAC_LINE + 6, T_EAC_LINE + 35],
		[0, 1],
		{
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: ease,
		},
	);

	// ── Date ──────────────────────────────────────────────────────────
	const dateSpring = spring({
		fps,
		frame: Math.max(0, frame - T_DATE),
		config: {damping: 200},
	});
	const dateScale = interpolate(dateSpring, [0, 1], [0.82, 1]);
	const dateOpacity = fadeIn(frame, T_DATE, 18);

	// ── Time ──────────────────────────────────────────────────────────
	const timeOpacity = fadeIn(frame, T_TIME);
	const timeTranslate = slideUp(frame, T_TIME);

	// ── Address ───────────────────────────────────────────────────────
	const addressOpacity = fadeIn(frame, T_ADDRESS);

	// ── CTA ───────────────────────────────────────────────────────────
	const ctaSpring = spring({
		fps,
		frame: Math.max(0, frame - T_CTA),
		config: {damping: 8, stiffness: 200, mass: 0.6},
	});
	const ctaScale = interpolate(ctaSpring, [0, 1], [0, 1]);
	const ctaOpacity = fadeIn(frame, T_CTA, 12);
	// Gentle pulse after entrance
	const cyclePos = (frame % 90) / 90;
	const triangle = cyclePos < 0.5 ? cyclePos * 2 : 2 - cyclePos * 2;
	const ctaPulse = frame > T_CTA + 30 ? interpolate(triangle, [0, 1], [0.98, 1.02]) : 1;
	const ctaFinal = ctaScale * ctaPulse;

	return (
		<AbsoluteFill style={{background: RED, overflow: 'hidden'}}>
			{/* ── PHOTO (fades in as frame expands) ─────────────────────── */}
			{/* Replace contents below with:
			       <Img src={staticFile('fille-cadre.jpg')} style={{width:'100%',height:'100%',objectFit:'cover'}} />
			    once public/fille-cadre.jpg is added. */}
			<div
				style={{
					position: 'absolute',
					left: photoX,
					top: photoY,
					width: photoW,
					height: photoH,
					opacity: photoOpacity,
					overflow: 'hidden',
				}}
			>
				{/* ── PLACEHOLDER: stylised silhouette on deep red ── */}
				{/* ── Swap with <Img> once photo is in public/       ── */}
				<svg
					width={photoW}
					height={photoH}
					viewBox="0 0 920 920"
					style={{display: 'block'}}
				>
					{/* Slightly deeper red background */}
					<rect width={920} height={920} fill="#B8000E" />
					{/* Subtle head silhouette */}
					<ellipse
						cx={460}
						cy={248}
						rx={108}
						ry={130}
						fill="rgba(255,255,255,0.10)"
					/>
					{/* Shoulders / body */}
					<path
						d="M 200 920 Q 210 560 460 500 Q 710 560 720 920 Z"
						fill="rgba(255,255,255,0.07)"
					/>
					{/* Arm holding frame — left */}
					<rect
						x={175}
						y={480}
						width={40}
						height={260}
						rx={20}
						fill="rgba(255,255,255,0.06)"
					/>
					{/* Arm — right */}
					<rect
						x={705}
						y={480}
						width={40}
						height={260}
						rx={20}
						fill="rgba(255,255,255,0.06)"
					/>
					{/* Inner held frame (smaller) */}
					<rect
						x={260}
						y={340}
						width={400}
						height={440}
						fill="none"
						stroke="rgba(255,255,255,0.18)"
						strokeWidth={14}
					/>
					{/* Photo-placeholder label */}
					<text
						x={460}
						y={920 - 30}
						textAnchor="middle"
						fontSize={20}
						fill="rgba(255,255,255,0.25)"
						fontFamily="Arial, sans-serif"
					>
						→ ajouter public/fille-cadre.jpg
					</text>
				</svg>
			</div>

			{/* ── LOGO → FRAME SVG ──────────────────────────────────────── */}
			<svg
				width={1080}
				height={1920}
				viewBox="0 0 1080 1920"
				style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}
			>
				{/* Growing white border rect — logo at first, frame at last */}
				<rect
					x={rX}
					y={rY}
					width={rW}
					height={rH}
					fill="none"
					stroke={WHITE}
					strokeWidth={FS}
					opacity={logoOpacity}
					style={{transformOrigin: `${FX + FW / 2}px ${FY + FH / 2}px`}}
				/>

				{/* E · A · C letters (fade out during morph) */}
				{lettersOpacity > 0.01 && (
					<g
						style={{
							opacity: lettersOpacity,
							fontFamily: FONT_FAMILY,
							fontWeight: 900,
							fill: WHITE,
							fontSize: letterFontSize,
							textAnchor: 'middle',
						}}
					>
						<text x={cx} y={eY + letterFontSize * 0.35}>
							E
						</text>
						<text x={cx} y={aY + letterFontSize * 0.35}>
							A
						</text>
						<text x={cx} y={cY + letterFontSize * 0.35}>
							C
						</text>
					</g>
				)}

				{/* Corner accent ticks — appear as frame finalises (F120→F145) */}
				{(['tl', 'tr', 'bl', 'br'] as const).map((corner) => {
					const tickOpacity = interpolate(
						frame,
						[T_MORPH_END - 10, T_MORPH_END + 20],
						[0, 1],
						{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
					);
					const len = 36;
					const gap = 8;
					const isLeft = corner === 'tl' || corner === 'bl';
					const isTop = corner === 'tl' || corner === 'tr';
					const cx2 = isLeft ? FX : FX + FW;
					const cy2 = isTop ? FY : FY + FH;
					const hDir = isLeft ? 1 : -1;
					const vDir = isTop ? 1 : -1;
					return (
						<g key={corner} opacity={tickOpacity}>
							<line
								x1={cx2 + hDir * gap}
								y1={cy2}
								x2={cx2 + hDir * (gap + len)}
								y2={cy2}
								stroke={WHITE}
								strokeWidth={3}
								opacity={0.5}
							/>
							<line
								x1={cx2}
								y1={cy2 + vDir * gap}
								x2={cx2}
								y2={cy2 + vDir * (gap + len)}
								stroke={WHITE}
								strokeWidth={3}
								opacity={0.5}
							/>
						</g>
					);
				})}
			</svg>

			{/* ── TEXT SECTION ──────────────────────────────────────────── */}
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: TEXT_TOP,
					width: 1080,
					paddingLeft: 80,
					paddingRight: 80,
					boxSizing: 'border-box',
				}}
			>
				{/* JOURNÉE PORTES OUVERTES — word by word */}
				<div
					style={{
						display: 'flex',
						flexWrap: 'wrap',
						gap: '0 14px',
						marginBottom: 6,
					}}
				>
					{words.map((word, i) => (
						<span
							key={word}
							style={{
								fontFamily: FONT_FAMILY,
								fontSize: 56,
								fontWeight: 700,
								color: WHITE,
								lineHeight: 1.15,
								opacity: wordOpacities[i],
								transform: `translateY(${wordTranslates[i]}px)`,
								display: 'inline-block',
							}}
						>
							{word}
						</span>
					))}
				</div>

				{/* EAC + full-width white divider */}
				<div
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: 18,
						marginBottom: 36,
						opacity: eacOpacity,
					}}
				>
					<span
						style={{
							fontFamily: FONT_FAMILY,
							fontSize: 48,
							fontWeight: 900,
							color: WHITE,
							letterSpacing: 8,
							flexShrink: 0,
						}}
					>
						EAC
					</span>
					<div
						style={{
							height: 3,
							background: WHITE,
							flex: 1,
							transformOrigin: 'left center',
							transform: `scaleX(${dividerScale})`,
							opacity: 0.55,
						}}
					/>
				</div>

				{/* 14 MARS */}
				<div
					style={{
						fontFamily: FONT_FAMILY,
						fontSize: 84,
						fontWeight: 900,
						color: WHITE,
						lineHeight: 1,
						marginBottom: 6,
						opacity: dateOpacity,
						transform: `scale(${dateScale})`,
						transformOrigin: 'left center',
						display: 'inline-block',
					}}
				>
					14 MARS
				</div>

				{/* 10H – 16H */}
				<div
					style={{
						fontFamily: FONT_FAMILY,
						fontSize: 44,
						fontWeight: 400,
						color: WHITE,
						opacity: timeOpacity * 0.85,
						transform: `translateY(${timeTranslate}px)`,
						marginBottom: 22,
						letterSpacing: 2,
					}}
				>
					10H – 16H
				</div>

				{/* 13 RUE MIOLLIS */}
				<div
					style={{
						fontFamily: FONT_FAMILY,
						fontSize: 36,
						fontWeight: 400,
						color: WHITE,
						opacity: addressOpacity * 0.72,
						letterSpacing: 1,
						marginBottom: 52,
					}}
				>
					13 RUE MIOLLIS
				</div>

				{/* RÉSERVE TA PLACE ! — white pill CTA */}
				<div
					style={{
						transform: `scale(${ctaFinal})`,
						transformOrigin: 'left center',
						opacity: ctaOpacity,
						display: 'inline-block',
					}}
				>
					<div
						style={{
							background: WHITE,
							borderRadius: 999,
							paddingTop: 22,
							paddingBottom: 22,
							paddingLeft: 52,
							paddingRight: 52,
							display: 'inline-block',
							boxShadow: '0 8px 40px rgba(0,0,0,0.25)',
						}}
					>
						<span
							style={{
								fontFamily: FONT_FAMILY,
								fontSize: 38,
								fontWeight: 700,
								color: RED,
								letterSpacing: 1,
								whiteSpace: 'nowrap',
							}}
						>
							RÉSERVE TA PLACE !
						</span>
					</div>
				</div>
			</div>
		</AbsoluteFill>
	);
};
