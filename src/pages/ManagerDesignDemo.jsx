import React, { useEffect, useState } from 'react';
import ManagerPanel from '../components/ManagerPanel';
import '../components/ManagerPanel.css';

export default function ManagerDesignDemo() {
  const [images, setImages] = useState([]);

  useEffect(() => {
    try {
      // Dynamically load all images under assets/managers
      const context = require.context('../assets/managers', false, /\.(png|jpe?g|gif|svg)$/);
      const imgs = context.keys().map((path) => context(path));
      setImages(imgs);
    } catch {
      // Fallback to a known list if dynamic import isn't supported
      setImages([
        '/Source_Code/src/assets/managers/manager_1.png',
        '/Source_Code/src/assets/managers/manager_2.png',
        '/Source_Code/src/assets/managers/manager_3.png',
      ]);
    }
  }, []);

  if (!images.length) return <div style={{ padding: '20px' }}>Loading managers...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <ManagerPanel images={images} />
    </div>
  );
}
