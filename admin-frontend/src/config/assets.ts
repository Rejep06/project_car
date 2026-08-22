const publicAsset = (name: string) =>
  `${import.meta.env.BASE_URL}assets/${name}`;

export const brandLogoUrl = publicAsset("logo.png");
export const defaultProgramImageUrl = publicAsset("program-car-photo.jpg");
