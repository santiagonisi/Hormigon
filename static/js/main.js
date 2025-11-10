document.addEventListener('DOMContentLoaded', () => {

  const btnTop = document.getElementById('scrollTopButton');
  if (btnTop) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) btnTop.classList.add('show');
      else btnTop.classList.remove('show');
    });
    btnTop.addEventListener('click', (e) => {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  const selectObra = document.getElementById('selectObra');
  const selectClase = document.getElementById('selectClase');

  if (selectObra && selectClase) {
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

  const checkProbetas = document.getElementById('checkProbetas');
  const probetasSection = document.getElementById('probetasSection');
  const tablaProbetas = document.getElementById('tablaProbetas');

  if (checkProbetas && probetasSection) {
    checkProbetas.addEventListener('change', () => {
      if (checkProbetas.checked) {
        probetasSection.style.display = 'block';
        generarFilasProbetas();
      } else {
        probetasSection.style.display = 'none';
        if (tablaProbetas) tablaProbetas.innerHTML = '';
      }
    });
  }

  function generarFilasProbetas(datos = null) {
    if (!tablaProbetas) return;
    tablaProbetas.innerHTML = '';
    for (let i = 1; i <= 3; i++) {
      const probeta = datos ? datos[i - 1] : null;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-center">${i}</td>
        <td><input type="date" class="form-control" name="fecha_ensayo_${i}" value="${probeta?.fecha_ensayo || ''}" /></td>
        <td><input type="number" class="form-control" name="edad_${i}" step="1" value="${probeta?.edad || probeta?.edad_dias || ''}" /></td>
        <td><input type="number" class="form-control" name="lectura_${i}" step="0.01" value="${probeta?.lectura || probeta?.lectura_prensa_kn || ''}" /></td>
        <td><input type="number" class="form-control" name="resistencia_${i}" step="0.01" value="${probeta?.resistencia || probeta?.resistencia_mpa || ''}" /></td>
      `;
      tablaProbetas.appendChild(tr);
    }
  }

  const parteForm = document.getElementById('parteForm');
  if (parteForm) {
    parteForm.addEventListener('submit', (ev) => {
      ev.preventDefault();

      const fecha = document.getElementById('fecha')?.value;
      const obra_id = document.getElementById('selectObra')?.value;
      const clase_id = document.getElementById('selectClase')?.value;
      const hora_despacho = document.getElementById('hora_despacho')?.value;
      const cantidad_m3 = document.getElementById('cantidad_m3')?.value;
      const asentamiento_cm = document.getElementById('asentamiento_cm')?.value;
      const usa_probetas = document.getElementById('checkProbetas')?.checked;

      const probetas = [];
      if (usa_probetas && tablaProbetas) {
        const rows = tablaProbetas.querySelectorAll('tr');
        rows.forEach((r, idx) => {
          const fecha_ensayo = r.querySelector(`input[name="fecha_ensayo_${idx+1}"]`)?.value || null;
          const edad = r.querySelector(`input[name="edad_${idx+1}"]`)?.value || null;
          const lectura = r.querySelector(`input[name="lectura_${idx+1}"]`)?.value || null;
          const resistencia = r.querySelector(`input[name="resistencia_${idx+1}"]`)?.value || null;
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(r => r.json())
        .then(resp => {
          if (resp.ok) {
            alert('Parte guardado correctamente. ID: ' + (resp.parte_id || ''));
            parteForm.reset();
            if (tablaProbetas) tablaProbetas.innerHTML = '';
            if (probetaSection) probetasSection.style.display = 'none';
            window.location.reload();
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

});
