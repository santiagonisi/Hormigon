// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
  // volver arriba
  const btnTop = document.getElementById('btnTop');
  window.onscroll = function () {
    if (!btnTop) return;
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
      btnTop.style.display = 'block';
    } else {
      btnTop.style.display = 'none';
    }
  };

  // PARTE DIARIO: actualizar select de clases cuando cambia la obra
  const selectObra = document.getElementById('selectObra');
  const selectClase = document.getElementById('selectClase');

  if (selectObra) {
    selectObra.addEventListener('change', (e) => {
      const obraId = e.target.value;
      selectClase.innerHTML = '<option value="">Cargando...</option>';
      if (!obraId) {
        selectClase.innerHTML = '<option value="">Seleccione obra primero</option>';
        return;
      }
      fetch(`/api/get_clases/${obraId}`)
        .then(res => res.json())
        .then(data => {
          selectClase.innerHTML = '<option value="">Seleccione clase</option>';
          data.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.nombre;
            selectClase.appendChild(opt);
          });
        })
        .catch(err => {
          console.error('Error cargando clases:', err);
          selectClase.innerHTML = '<option value="">Error al cargar</option>';
        });
    });
  }

  // PROBETAS: mostrar/ocultar y generar 3 filas
  const checkProbetas = document.getElementById('checkProbetas');
  const probetasSection = document.getElementById('probetasSection');
  const tablaProbetas = document.getElementById('tablaProbetas');

  if (checkProbetas) {
    checkProbetas.addEventListener('change', () => {
      if (checkProbetas.checked) {
        probetasSection.style.display = 'block';
        generarFilasProbetas();
      } else {
        probetasSection.style.display = 'none';
        tablaProbetas.innerHTML = '';
      }
    });
  }

  function generarFilasProbetas() {
    tablaProbetas.innerHTML = '';
    for (let i = 1; i <= 3; i++) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-center">${i}</td>
        <td><input type="date" class="form-control" name="fecha_ensayo_${i}" /></td>
        <td><input type="number" class="form-control" name="edad_${i}" step="1" /></td>
        <td><input type="number" class="form-control" name="lectura_${i}" step="0.01" /></td>
        <td><input type="number" class="form-control" name="resistencia_${i}" step="0.01" readonly /></td>
      `;
      tablaProbetas.appendChild(tr);
    }
  }

  // Envío del formulario parte diario por fetch (json)
  const parteForm = document.getElementById('parteForm');
  if (parteForm) {
    parteForm.addEventListener('submit', (ev) => {
      ev.preventDefault();
      // recolectar datos
      const fecha = document.getElementById('fecha').value;
      const obra_id = document.getElementById('selectObra').value;
      const clase_id = document.getElementById('selectClase').value;
      const hora_despacho = document.getElementById('hora_despacho').value;
      const cantidad_m3 = document.getElementById('cantidad_m3').value;
      const asentamiento_cm = document.getElementById('asentamiento_cm').value;
      const usa_probetas = document.getElementById('checkProbetas').checked;

      const probetas = [];
      if (usa_probetas) {
        const rows = tablaProbetas.querySelectorAll('tr');
        rows.forEach((r, idx) => {
          const fecha_ensayo = r.querySelector(`input[name="fecha_ensayo_${idx+1}"]`).value;
          const edad = r.querySelector(`input[name="edad_${idx+1}"]`).value;
          const lectura = r.querySelector(`input[name="lectura_${idx+1}"]`).value;
          const resistencia = r.querySelector(`input[name="resistencia_${idx+1}"]`).value;
          probetas.push({
            fecha_ensayo: fecha_ensayo || null,
            edad: edad || null,
            lectura: lectura || null,
            resistencia: resistencia || null
          });
        });
      }

      const payload = {
        fecha, obra_id, clase_id, hora_despacho, cantidad_m3, asentamiento_cm, usa_probetas, probetas
      };

      fetch('/api/guardar_parte', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.ok) {
          alert('Parte guardado correctamente. ID: ' + resp.parte_id);
          parteForm.reset();
          tablaProbetas.innerHTML = '';
          probetasSection.style.display = 'none';
        } else {
          alert('Error: ' + (resp.error || 'Error desconocido'));
        }
      })
      .catch(err => {
        console.error(err);
        alert('Error guardando parte. Revisá la consola.');
      });
    });
  }

  // FORMULAS: agregar filas dinámicas y eliminar
  const agregarFilaBtn = document.getElementById('agregarFila');
  const tablaMateriales = document.getElementById('tablaMateriales');
  if (agregarFilaBtn) {
    let contador = 0;
    agregarFilaBtn.addEventListener('click', () => {
      contador++;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-center">${contador}</td>
        <td><input type="text" name="material_${contador}" class="form-control" required></td>
        <td><input type="number" step="0.01" name="cantidad_${contador}" class="form-control" required></td>
        <td>
          <select name="unidad_${contador}" class="form-select">
            <option value="kg">kg</option>
            <option value="m3">m³</option>
            <option value="lts">lts</option>
            <option value="unidades">unidades</option>
          </select>
        </td>
        <td class="text-center">
          <button type="button" class="btn btn-sm btn-danger eliminar-fila"><i class="bi bi-trash"></i></button>
        </td>
      `;
      tablaMateriales.appendChild(tr);
    });

    tablaMateriales.addEventListener('click', (e) => {
      if (e.target.closest('.eliminar-fila')) {
        e.target.closest('tr').remove();
      }
    });

    // envío de formulario formulas (temporal: solo muestra alerta)
    const formFormula = document.getElementById('formFormula');
    if (formFormula) {
      formFormula.addEventListener('submit', (ev) => {
        ev.preventDefault();
        alert('Aquí se podría guardar la fórmula en la base de datos (implementación pendiente).');
      });
    }
  }
});
