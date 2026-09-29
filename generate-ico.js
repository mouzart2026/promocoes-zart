const sharp = require('sharp');
const fs = require('fs');

const inputSvg = 'assets/img/brand/icons/favicon-promozart.svg';
const outputIco = 'assets/img/brand/icons/favicon-promozart.ico';

const sizes = [16, 32, 48];

async function generateIco() {
    const buffers = await Promise.all(
        sizes.map(async (size) => {
            const buf = await sharp(inputSvg).resize(size, size).toBuffer();
            return buf;
        })
    );

    // Build ICO file manually
    const HEADER_SIZE = 6;
    const DIRECTORY_ENTRY_SIZE = 16;
    const numImages = buffers.length;
    
    const header = Buffer.alloc(HEADER_SIZE);
    header.writeUInt16LE(0, 0); // Reserved
    header.writeUInt16LE(1, 2); // Type: ICO
    header.writeUInt16LE(numImages, 4); // Number of images

    const directory = Buffer.alloc(DIRECTORY_ENTRY_SIZE * numImages);
    let offset = HEADER_SIZE + DIRECTORY_ENTRY_SIZE * numImages;

    for (let i = 0; i < numImages; i++) {
        const size = Math.min(sizes[i], 256);
        directory.writeUInt8(size === 256 ? 0 : size, i * DIRECTORY_ENTRY_SIZE + 0); // Width
        directory.writeUInt8(size === 256 ? 0 : size, i * DIRECTORY_ENTRY_SIZE + 1); // Height
        directory.writeUInt8(0, i * DIRECTORY_ENTRY_SIZE + 2); // Color palette count
        directory.writeUInt8(0, i * DIRECTORY_ENTRY_SIZE + 3); // Reserved
        directory.writeUInt16LE(1, i * DIRECTORY_ENTRY_SIZE + 4); // Color planes
        directory.writeUInt16LE(32, i * DIRECTORY_ENTRY_SIZE + 6); // Bits per pixel
        directory.writeUInt32LE(buffers[i].length, i * DIRECTORY_ENTRY_SIZE + 8); // Size of image data (offset +8)
        directory.writeUInt32LE(offset, i * DIRECTORY_ENTRY_SIZE + 12); // Offset of image data (offset +12)
        offset += buffers[i].length;
    }

    const ico = Buffer.concat([header, directory, ...buffers]);
    fs.writeFileSync(outputIco, ico);
    console.log(`Generated: ${outputIco} (${ico.length} bytes)`);
}

generateIco().catch(console.error);
