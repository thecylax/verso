import { describe, expect, it } from 'vitest';
import { refreshMessage, saveFailureMessage } from './passageStatus';

describe('refreshMessage', () => {
	it('fica em silêncio quando nada mudou', () => {
		expect(refreshMessage({ updated: 0, failed: 0 })).toBeNull();
	});

	it('confirma quando tudo foi atualizado', () => {
		expect(refreshMessage({ updated: 2, failed: 0 })).toEqual({
			kind: 'success',
			message: 'Versículos atualizados: 2 passagens.'
		});
	});

	it('avisa quando ainda falta texto', () => {
		expect(refreshMessage({ updated: 0, failed: 1 })?.kind).toBe('warning');
		expect(refreshMessage({ updated: 0, failed: 1 })?.message).toContain('Não foi possível buscar 1 passagem.');
		expect(refreshMessage({ updated: 1, failed: 3 })?.message).toContain('Ainda sem texto: 3 passagens.');
	});
});

describe('saveFailureMessage', () => {
	it('usa singular e plural', () => {
		expect(saveFailureMessage(1)).toContain('1 passagem.');
		expect(saveFailureMessage(4)).toContain('4 passagens.');
	});
});
