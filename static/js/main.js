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

});
