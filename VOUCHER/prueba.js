import React, { useState, useRef } from 'react';
import { Upload, Download, FileText, Edit3 } from 'lucide-react';

export default function VoucherEditor() {
  const [image, setImage] = useState(null);
  const [formData, setFormData] = useState({
    numeroRecibo: '1124-20-4',
    fecha: '17/06/2025',
    hora: '12:09:16',
    monto: '20.70',
    nombre: 'LOPEZ MALCA STIVEN ADRIAN',
    carnet: '1023300123',
    escuela: 'INGENIERIA DE SISTEMAS',
    montoPalabras: 'VEINTE Y 70/100 NUEVOS SOLES',
    concepto: 'CARNET UNIVERSITARIO',
    serie: '0077349'
  });
  
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const generateVoucher = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Establecer dimensiones del canvas
    canvas.width = 1200;
    canvas.height = 900;
    
    // Fondo blanco
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Encabezado verde
    ctx.fillStyle = '#2d7a3e';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('UNIVERSIDAD NACIONAL DE TRUJILLO', 600, 60);
    
    ctx.font = 'bold 20px Arial';
    ctx.fillText('DIRECCIÓN DE TESORERÍA', 600, 90);
    ctx.fillText('ÁREA DE GESTIÓN DE INGRESOS', 600, 115);
    ctx.fillText('Diego de Almagro N° 344 - TRUJILLO - PERÚ', 600, 140);
    ctx.font = '18px Arial';
    ctx.fillText('R.U.C. 20172857628', 600, 165);
    
    ctx.font = 'bold 36px Arial';
    ctx.fillText('RECIBO DE CAJA', 600, 210);
    
    // Número de recibo (derecha)
    ctx.font = 'bold 28px Courier New';
    ctx.textAlign = 'right';
    ctx.fillText(formData.numeroRecibo, 1100, 260);
    
    // Información de línea 1
    ctx.font = '18px Courier New';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#000000';
    ctx.fillText(`TASA : 20  VENT:4      CTA.IP:122 .03.01 .01.01    SIAF:132.311`, 80, 320);
    
    // Fecha, hora y monto
    ctx.font = 'bold 20px Courier New';
    ctx.fillText(`FECHA : ${formData.fecha}    HORA : ${formData.hora}    S/. ${formData.monto}`, 80, 360);
    
    // Información del receptor
    ctx.font = '18px Courier New';
    ctx.fillText(`HE RECIBIDO DE : ${formData.nombre} CARNET: ${formData.carnet}`, 80, 420);
    
    // Escuela
    ctx.fillText(`ESCUELA         : ${formData.escuela}`, 80, 460);
    
    // Suma de
    ctx.fillText(`   LA SUMA DE   : ${formData.montoPalabras}`, 80, 500);
    
    // Concepto
    ctx.fillText(`POR CONCEPTO DE:`, 80, 540);
    ctx.fillText(`      ${formData.concepto}`, 80, 580);
    
    // Serie (abajo izquierda)
    ctx.font = 'bold 24px Arial';
    ctx.fillStyle = '#2d7a3e';
    ctx.fillText('Serie N° 1', 80, 820);
    
    // Número de serie (abajo derecha)
    ctx.font = 'bold 48px Arial';
    ctx.fillStyle = '#ff4444';
    ctx.textAlign = 'right';
    ctx.fillText(formData.serie, 1100, 820);
    
    // Círculos perforados a la derecha
    ctx.fillStyle = '#333333';
    for (let i = 0; i < 8; i++) {
      ctx.beginPath();
      ctx.arc(1150, 100 + i * 100, 15, 0, 2 * Math.PI);
      ctx.fill();
    }
  };

  const downloadVoucher = () => {
    generateVoucher();
    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `voucher_${formData.serie}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 text-white">
            <div className="flex items-center gap-3">
              <FileText size={36} />
              <div>
                <h1 className="text-3xl font-bold">Editor de Vouchers UNT</h1>
                <p className="text-green-100 mt-1">Universidad Nacional de Trujillo</p>
              </div>
            </div>
          </div>

          <div className="p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Panel Izquierdo - Formulario */}
              <div className="space-y-6">
                <div className="bg-blue-50 p-6 rounded-xl border-2 border-blue-200">
                  <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <Edit3 size={24} className="text-blue-600" />
                    Datos del Voucher
                  </h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Número de Recibo (XXXX-XX-X)
                      </label>
                      <input
                        type="text"
                        value={formData.numeroRecibo}
                        onChange={(e) => handleInputChange('numeroRecibo', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                        placeholder="1124-20-4"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          Fecha
                        </label>
                        <input
                          type="text"
                          value={formData.fecha}
                          onChange={(e) => handleInputChange('fecha', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                          placeholder="DD/MM/YYYY"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          Hora
                        </label>
                        <input
                          type="text"
                          value={formData.hora}
                          onChange={(e) => handleInputChange('hora', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                          placeholder="HH:MM:SS"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Monto (S/.)
                      </label>
                      <input
                        type="text"
                        value={formData.monto}
                        onChange={(e) => handleInputChange('monto', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                        placeholder="20.70"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Nombre Completo
                      </label>
                      <input
                        type="text"
                        value={formData.nombre}
                        onChange={(e) => handleInputChange('nombre', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Carnet
                      </label>
                      <input
                        type="text"
                        value={formData.carnet}
                        onChange={(e) => handleInputChange('carnet', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Escuela
                      </label>
                      <input
                        type="text"
                        value={formData.escuela}
                        onChange={(e) => handleInputChange('escuela', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Monto en Palabras
                      </label>
                      <input
                        type="text"
                        value={formData.montoPalabras}
                        onChange={(e) => handleInputChange('montoPalabras', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Concepto
                      </label>
                      <input
                        type="text"
                        value={formData.concepto}
                        onChange={(e) => handleInputChange('concepto', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Serie (XXXXXXX)
                      </label>
                      <input
                        type="text"
                        value={formData.serie}
                        onChange={(e) => handleInputChange('serie', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-green-500 focus:outline-none"
                        placeholder="0077349"
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={downloadVoucher}
                  className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-4 rounded-xl font-bold text-lg hover:from-green-700 hover:to-green-800 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3"
                >
                  <Download size={24} />
                  Generar y Descargar Voucher
                </button>
              </div>

              {/* Panel Derecho - Vista Previa */}
              <div className="space-y-4">
                <div className="bg-gray-50 p-6 rounded-xl border-2 border-gray-200">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">
                    Vista Previa
                  </h2>
                  <canvas
                    ref={canvasRef}
                    className="w-full border-4 border-gray-300 rounded-lg shadow-lg bg-white"
                    onClick={generateVoucher}
                  />
                  <p className="text-sm text-gray-500 mt-2 text-center">
                    Haz clic en el canvas o en el botón para actualizar la vista previa
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}