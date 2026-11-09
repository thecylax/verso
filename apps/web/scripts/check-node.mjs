const [major, minor] = process.versions.node.split('.').map(Number);

if (major < 22 || (major === 22 && minor < 14)) {
	console.error(`Node ${process.versions.node} encontrado; o front precisa de 22.14 ou mais novo (ex.: nvm use 22).`);
	process.exit(1);
}
