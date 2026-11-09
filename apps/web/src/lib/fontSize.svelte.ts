import {
	FONT_STEP,
	FONT_STORAGE_KEY,
	clampFontSize,
	parseStoredFontSize,
	pinchFontSize
} from './zoom';

function readStored(): number {
	try {
		return parseStoredFontSize(localStorage.getItem(FONT_STORAGE_KEY));
	} catch {
		return parseStoredFontSize(null);
	}
}

export const reading = $state({ fontSize: typeof localStorage === 'undefined' ? 18 : readStored() });

export function setFontSize(value: number, persist = true): void {
	reading.fontSize = clampFontSize(value);
	if (persist) {
		try {
			localStorage.setItem(FONT_STORAGE_KEY, String(reading.fontSize));
		} catch {
			// armazenamento indisponível: a preferência vale só nesta sessão
		}
	}
}

export const zoomIn = () => setFontSize(reading.fontSize + FONT_STEP);
export const zoomOut = () => setFontSize(reading.fontSize - FONT_STEP);

/** Ação Svelte: pinça com dois ponteiros e Ctrl/Meta + roda na área de leitura. */
export function pinchZoom(node: HTMLElement) {
	const pointers = new Map<number, { x: number; y: number }>();
	let initialDistance = 0;
	let initialSize = reading.fontSize;

	const distance = () => {
		const [a, b] = [...pointers.values()];
		return Math.hypot(a.x - b.x, a.y - b.y);
	};

	function onDown(event: PointerEvent) {
		if (event.pointerType === 'mouse') return;
		pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
		if (pointers.size === 2) {
			initialDistance = distance();
			initialSize = reading.fontSize;
		}
	}

	function onMove(event: PointerEvent) {
		if (!pointers.has(event.pointerId)) return;
		pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
		if (pointers.size === 2) {
			event.preventDefault();
			setFontSize(pinchFontSize(initialSize, initialDistance, distance()), false);
		}
	}

	function onUp(event: PointerEvent) {
		if (!pointers.delete(event.pointerId)) return;
		if (pointers.size < 2 && initialDistance > 0) {
			initialDistance = 0;
			setFontSize(reading.fontSize);
		}
	}

	function onWheel(event: WheelEvent) {
		if (!event.ctrlKey && !event.metaKey) return;
		event.preventDefault();
		if (event.deltaY < 0) zoomIn();
		else if (event.deltaY > 0) zoomOut();
	}

	node.style.touchAction = 'pan-y';
	node.addEventListener('pointerdown', onDown);
	node.addEventListener('pointermove', onMove, { passive: false });
	node.addEventListener('pointerup', onUp);
	node.addEventListener('pointercancel', onUp);
	node.addEventListener('wheel', onWheel, { passive: false });

	return {
		destroy() {
			node.removeEventListener('pointerdown', onDown);
			node.removeEventListener('pointermove', onMove);
			node.removeEventListener('pointerup', onUp);
			node.removeEventListener('pointercancel', onUp);
			node.removeEventListener('wheel', onWheel);
		}
	};
}
