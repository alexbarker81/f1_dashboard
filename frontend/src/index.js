import React from 'react';
import ReactDOM from 'react-dom/client'; // For React 18+
import './index.css'; // You can create a basic index.css or remove this line if not needed
import App from './App';
import reportWebVitals from './reportWebVitals'; // You can remove this if not using web-vitals

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
