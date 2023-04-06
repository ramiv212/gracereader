async function createResizedImage (file, size) {
    size ??= 900
  
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
  
    const bitmap = await createImageBitmap(file)
    const { width, height } = bitmap

    const ratio = Math.max(size / width, size / height)

    canvas.width = width * ratio
    canvas.height = height * ratio
  
  
    ctx.drawImage(bitmap, 0, 0, width, height, 0, 0, width * ratio, height * ratio)
  
    return new Promise(resolve => {
      canvas.toBlob(blob => {
        resolve(blob)
      }, 'image/webp', .6)
    })
  }
  