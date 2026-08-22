const publicAsset = (name: string) =>
  `${import.meta.env.BASE_URL}assets/${name}`;

export const brandLogoUrl = publicAsset("logo.png");
export const heroCarPhotoUrl = publicAsset("hero-car-photo.jpg");
export const defaultProgramImageUrl = publicAsset("program-car-photo.jpg");
