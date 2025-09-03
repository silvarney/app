const { execSync } = require('child_process');
const path = require('path');

const inputPath = path.join(__dirname, 'static', 'css', 'input.css');
const outputPath = path.join(__dirname, 'static', 'css', 'output.css');

try {
  console.log('Building Tailwind CSS...');
  execSync(`npx tailwindcss -i ${inputPath} -o ${outputPath} --watch`, {
    stdio: 'inherit'
  });
} catch (error) {
  console.error('Error building CSS:', error.message);
  process.exit(1);
}