dist/main.js: src/main.ts
	pnpm tsc --outDir dist $<

clean:
	rm main.js
