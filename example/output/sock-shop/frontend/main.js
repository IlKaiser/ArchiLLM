import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);
  useEffect(() => {
    axios.get('/api/catalog/products').then(res => setProducts(res.data));
  }, []);
  return (
    <div>
      <h1>SockShop Catalog</h1>
      <ul>
        {products.map(p => (
          <li key={p.id}>{p.name} - ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
ReactDOM.render(<App />, document.getElementById('root'));