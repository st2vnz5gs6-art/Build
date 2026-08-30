// One-off placeholder icon generator (no image deps): writes solid PNGs with
// a centered accent dot so the PWA has real icon files out of the box.
// Swap public/icons/*.png for real branding whenever — this is just a stand-in.
import { deflateSync } from "node:zlib";
import { writeFileSync } from "node:fs";

const CRC_TABLE = (() => {
  const table = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuf = Buffer.from(type, "ascii");
  const lenBuf = Buffer.alloc(4);
  lenBuf.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([lenBuf, typeBuf, data, crcBuf]);
}

function makePng(size, { bg, fg, radiusRatio }) {
  const raw = Buffer.alloc((size * 4 + 1) * size);
  const cx = size / 2;
  const cy = size / 2;
  const r = size * radiusRatio;
  for (let y = 0; y < size; y++) {
    const rowStart = y * (size * 4 + 1);
    raw[rowStart] = 0; // filter type: none
    for (let x = 0; x < size; x++) {
      const dx = x - cx;
      const dy = y - cy;
      const inCircle = dx * dx + dy * dy <= r * r;
      const [rr, gg, bb, aa] = inCircle ? fg : bg;
      const off = rowStart + 1 + x * 4;
      raw[off] = rr;
      raw[off + 1] = gg;
      raw[off + 2] = bb;
      raw[off + 3] = aa;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // color type: RGBA
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const idat = deflateSync(raw);
  return Buffer.concat([signature, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0))]);
}

const bg = [10, 11, 13, 255]; // ink-950
const fg = [79, 124, 255, 255]; // accent

for (const size of [192, 512]) {
  const png = makePng(size, { bg, fg, radiusRatio: 0.34 });
  writeFileSync(`public/icons/icon-${size}.png`, png);
  console.log(`wrote public/icons/icon-${size}.png`);
}

const maskable = makePng(512, { bg, fg, radiusRatio: 0.28 });
writeFileSync("public/icons/maskable-512.png", maskable);
console.log("wrote public/icons/maskable-512.png");
