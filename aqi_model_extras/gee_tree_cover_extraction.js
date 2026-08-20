// ============================================================
// Tree Cover Extraction — Delhi NCR
// Dataset: ESA WorldCover 10m v200 (2021) — free, CC-BY-4.0
// Run this in the GEE Code Editor: code.earthengine.google.com
// ============================================================

// Same bbox used for your pollutant concentration rasters, for alignment
var ncrBbox = ee.Geometry.Rectangle([76.698, 28.099, 77.704, 28.908]);

// Load the WorldCover image
var worldCover = ee.Image('ESA/WorldCover/v200');

// Class 10 = "Tree cover". Create a binary mask: 1 = tree, 0 = not tree.
var treeMask = worldCover.select('Map').eq(10);

// Clip to Delhi NCR
var treeCoverNCR = treeMask.clip(ncrBbox);

// Visualize (optional, for sanity check in the GEE preview map)
Map.centerObject(ncrBbox, 10);
Map.addLayer(treeCoverNCR, {min: 0, max: 1, palette: ['000000', '00FF00']}, 'Tree Cover (green = trees)');

// Export as GeoTIFF to your Google Drive (same workflow as your pollutant rasters)
Export.image.toDrive({
  image: treeCoverNCR,
  description: 'DelhiNCR_TreeCover_2021',
  folder: 'GEE_Exports',
  fileNamePrefix: 'DelhiNCR_TreeCover_2021',
  region: ncrBbox,
  scale: 10,          // native 10m resolution
  crs: 'EPSG:4326',
  maxPixels: 1e9
});

// Optional: also compute tree-cover % for a specific point/radius directly in GEE
// (useful for a quick sanity check before building the full backend pipeline)
var testPoint = ee.Geometry.Point([77.3152, 28.6469]).buffer(2000); // Anand Vihar, 2km radius
var treeFraction = treeCoverNCR.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: testPoint,
  scale: 10,
  maxPixels: 1e9
});
print('Anand Vihar 2km tree-cover fraction:', treeFraction);
