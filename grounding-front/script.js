var spacing_count = 0;
var resistances_count = 0;

window.addEventListener("load", function() {
	document.getElementById("add").addEventListener("click", function() {
		spacing_count++;
		resistances_count++;

		var div = document.createElement("div");
		div.setAttribute("class", "measurement");
		
		var label_spacing = document.createElement("label");
		label_spacing.setAttribute("for", "spacing" + spacing_count);
		label_spacing.innerHTML = "Espaçamento (m): ";

		var input_spacing = document.createElement("input");
		input_spacing.setAttribute("type", "number");
		input_spacing.setAttribute("name", "spacing" + spacing_count);
		input_spacing.setAttribute("class", "spacing");
		input_spacing.setAttribute("min", 1);

		var label_resistances = document.createElement("label");
		label_resistances.setAttribute("for", "resistances" + resistances_count);
		label_resistances.innerHTML = " Resistências (ohm): ";

		var input_resistances = document.createElement("input");
		input_resistances.setAttribute("type", "text");
		input_resistances.setAttribute("name", "resistances" + resistances_count);
		input_resistances.setAttribute("class", "resistances");
		input_resistances.setAttribute("min", 0);
	
		div.appendChild(label_spacing);
		div.appendChild(input_spacing);
		div.appendChild(label_resistances);
		div.appendChild(input_resistances);
	
		document.getElementById("container").appendChild(div);
	});

	document.getElementById("remove").addEventListener("click", function() {
		spacing_count = 0;
		resistances_count = 0;
		document.getElementById("container").innerHTML = "&nbsp;";
	});

	document.getElementById("test_grid").addEventListener("click", function() {
		const url = 'https://quiet-beyond-96020.herokuapp.com/api/';
//		const url = 'http://127.0.0.1:8000/api/';
		const data = JSON.stringify(generate_data_object());
		if (data == undefined) {
			return;
		}
		const params = {
			headers: {
			  'content-type': 'application/json'
			},
			method: 'POST',
			body: data
		};
		fetch(url, params)
			.then(data => {console.log(data); return data.json()})
			.then(res => {console.log(res); update_screen(res)})
			.catch(e => {
				console.log(e);
				alert('Erro. Provavelmente na estratificação ou na geração do gráfico.');
			})
	});

});

function generate_data_object() {
	var rod_depth = document.getElementById("rod-depth").value;
	if (rod_depth == '' || rod_depth <= 0) {
		alert('Profundidade da haste vazia.');
		return;
	}

	var spacings = document.getElementsByClassName("spacing");
	var resistances_lists = document.getElementsByClassName("resistances");
	if (spacings.length == 0 || resistances_lists.length == 0) {
		alert('Não foram inseridas medições.');
		return;
	}

	var spacings_list = [];
	for (var i = 0; i < spacings.length; i++) {
		var spacing = spacings[i].value;
		if (spacing == '' || spacing <= 0) {
			alert('As medições possuem espaçamentos vazios ou iguais a 0.');
			return;
		}
		spacings_list.push(parseFloat(spacing));
	}

	var resistances_list = [];
	for (var i = 0; i < resistances_lists.length; i++) {
		var resistances = resistances_lists[i].value.split(',').map(Number);
		var includes_zero = resistances.includes(0);
		if (includes_zero) {
			alert('As medições possuem resistências vazias ou iguais a 0.');
			return;
		}
		resistances_list.push(resistances);
	}

	var resistance_length = [];
	const allEqual = arr => arr.every( v => v === arr[0] );
	for (var i = 0; i < resistances_list.length; i++) {
		resistance_length.push(resistances_list[i].length);
	}
	if (!allEqual(resistance_length)) {
		alert('Os espaçamentos devem ter o mesmo número de medições de resistência.');
		return;
	}

	var measurements = {
		"spacing": spacings_list,
		"resistances": resistances_list
	};

	var current_phase_ground = document.getElementById("current-phase-ground").value;
	if (current_phase_ground == '' || current_phase_ground <= 0) {
		alert('Corrente fase-terra vazia.');
		return;
	}

	var current_grid = document.getElementById("current-grid").value;
	if (current_grid == '' || current_grid <= 0) {
		alert('Corrente na malha vazia.');
		return;
	}

	var defect_duration = document.getElementById("defect-duration").value;
	if (defect_duration == '' || defect_duration <= 0) {
		alert('Duração da falta vazia.');
		return;
	}

	var grid_width = document.getElementById("grid-width").value;
	if (grid_width == '' || grid_width <= 0) {
		alert('Largura da malha vazia.');
		return;
	}

	var grid_length = document.getElementById("grid-length").value;
	if (grid_length == '' || grid_length <= 0) {
		alert('Comprimento da malha vazio.');
		return;
	}

	var ea = document.getElementById("ea").value;
	if (ea == '' || ea <= 0) {
		alert('Espaçamento entre condutores no eixo X vazio.');
		return;
	}

	var eb = document.getElementById("eb").value;
	if (eb == '' || eb <= 0) {
		alert('Espaçamento entre condutores no eixo Y vazio.');
		return;
	}

	var grid_height = document.getElementById("grid-height").value;
	if (grid_height == '' || grid_height <= 0) {
		alert('Profundidade da malha vazia.');
		return;
	}

	var rod_height = document.getElementById("rod-height").value;
	if (rod_height == '' || rod_height <= 0) {
		alert('Altura da haste vazia.');
		return;
	}

	var gravel_resistivity = document.getElementById("gravel-resistivity").value;
	if (gravel_resistivity == '' || gravel_resistivity < 0) {
		alert('Resistividade da brita vazia ou negativa.');
		return;
	}

	var gravel_height = document.getElementById("gravel-height").value;
	if (gravel_height == '' || gravel_height < 0) {
		alert('Altura da camada de brita vazia ou negativa.');
		return;
	}

	if (gravel_resistivity == 0 && gravel_height != 0) {
		alert('A resistividade da brita indica que a altura da camada de brita deve ser zero.');
		return;
	}

	if (gravel_height == 0 && gravel_resistivity != 0) {
		alert('A altura da camada de brita indica que a resistividade da brita deve ser zero.');
	}

	const data = {
		"rod-depth": parseFloat(rod_depth),
		"measurements": measurements,
		"current-phase-ground": parseFloat(current_phase_ground),
		"current-grid": parseFloat(current_grid),
		"defect-duration": parseFloat(defect_duration),
		"grid-width": parseFloat(grid_width),
		"grid-length": parseFloat(grid_length),
		"ea": parseFloat(ea),
		"eb": parseFloat(eb),
		"grid-height": parseFloat(grid_height),
		"rod-height": parseFloat(rod_height),
		"gravel-resistivity": parseFloat(gravel_resistivity),
		"gravel-height": parseFloat(gravel_height)
	}

	return data;
}

function update_screen(data) {

	alert('Cálculos feitos com sucesso.');

	var spacing = data['spacing'].map(n => {
		return (Math.round(n * 10) / 10).toFixed(1);
	});
	var resistivities = data['resistivities'].map(n => {
		return (Math.round(n * 10) / 10).toFixed(1);
	});
	var first_layer_resistivity = (Math.round(data['first-layer-resistivity'] * 10) / 10).toFixed(1);
	var first_layer_depth = (Math.round(data['first-layer-depth'] * 10) / 10).toFixed(1);
	var second_layer_resistivity = (Math.round(data['second-layer-resistivity'] * 10) / 10).toFixed(1);
	var is_grid_safe = "";
	if (data['is-grid-safe']) {
		is_grid_safe = "A malha atende aos critérios de segurança.";
	} else {
		is_grid_safe = "A malha não atende aos critérios de segurança.";
	}
	var number_of_conductors_x_axis = (Math.round(data['number-of-conductors-x-axis'] * 10) / 10).toFixed(1);
	var conductor_spacing_x_axis = (Math.round(data['conductor-spacing-x-axis'] * 10) / 10).toFixed(1);
	var number_of_conductors_y_axis = (Math.round(data['number-of-conductors-y-axis'] * 10) / 10).toFixed(1);
	var conductor_spacing_y_axis = (Math.round(data['conductor-spacing-y-axis'] * 10) / 10).toFixed(1);
	var grid_conductors_gauge = (Math.round(data['grid-conductors-gauge'] * 10) / 10).toFixed(1);
	var connection_cable_gauge = (Math.round(data['connection-cable-gauge'] * 10) / 10).toFixed(1);
	var total_length = (Math.round(data['total-length'] * 10) / 10).toFixed(1);
	var number_of_rods = (Math.round(data['number-of-rods'] * 10) / 10).toFixed(1);
	var maximum_touch_voltage = (Math.round(data['maximum-touch-voltage'] * 10) / 10).toFixed(1);
	var maximum_step_voltage = (Math.round(data['maximum-step-voltage'] * 10) / 10).toFixed(1);
	var grid_touch_voltage = (Math.round(data['grid-touch-voltage'] * 10) / 10).toFixed(1);
	var grid_step_voltage = (Math.round(data['grid-step-voltage'] * 10) / 10).toFixed(1);
	var fence_touch_voltage = (Math.round(data['fence-touch-voltage'] * 10) / 10).toFixed(1);
	var grid_resistance = (Math.round(data['grid-resistance'] * 10) / 10).toFixed(1);

	document.getElementById("spacing").setAttribute("value", spacing);
	document.getElementById("resistivities").setAttribute("value", resistivities);
	document.getElementById("first-layer-resistivity").setAttribute("value", first_layer_resistivity);
	document.getElementById("first-layer-depth").setAttribute("value", first_layer_depth);
	document.getElementById("second-layer-resistivity").setAttribute("value", second_layer_resistivity);
	document.getElementById("is-grid-safe").setAttribute("value", is_grid_safe);
	document.getElementById("number-of-conductors-x-axis").setAttribute("value", number_of_conductors_x_axis);
	document.getElementById("conductor-spacing-x-axis").setAttribute("value", conductor_spacing_x_axis);
	document.getElementById("number-of-conductors-y-axis").setAttribute("value", number_of_conductors_y_axis);
	document.getElementById("conductor-spacing-y-axis").setAttribute("value", conductor_spacing_y_axis);
	document.getElementById("grid-conductors-gauge").setAttribute("value", grid_conductors_gauge);
	document.getElementById("connection-cable-gauge").setAttribute("value", connection_cable_gauge);
	document.getElementById("total-length").setAttribute("value", total_length);
	document.getElementById("number-of-rods").setAttribute("value", number_of_rods);
	document.getElementById("maximum-touch-voltage").setAttribute("value", maximum_touch_voltage);
	document.getElementById("maximum-step-voltage").setAttribute("value", maximum_step_voltage);
	document.getElementById("grid-touch-voltage").setAttribute("value", grid_touch_voltage);
	document.getElementById("grid-step-voltage").setAttribute("value", grid_step_voltage);
	document.getElementById("fence-touch-voltage").setAttribute("value", fence_touch_voltage);
	document.getElementById("grid-resistance").setAttribute("value", grid_resistance);

	var ctx_resistivity = document.getElementById('resistivities_chart').getContext('2d');

	resistivity_data = []

	for (var i = 0; i < spacing.length; i++) {
		var point = {
			"x": spacing[i],
			"y": resistivities[i]
		};
		resistivity_data.push(point);
	}

	var chart_resistivity = new Chart(ctx_resistivity, {
		type: 'scatter',
		data: {
			datasets: [{
				label: 'Resistividades',
				data: resistivity_data,
				backgroundColor: 'rgb(0, 0, 0)',
				borderColor: 'rgb(0, 0, 0)',
			}]
		},
		options: {
			events: []
		}
	});

	var ctx_stratification = document.getElementById('stratification_chart').getContext('2d');

	var resistivity_curve_data = data['resistivity-curve-data'];
	var spacing_curve_data = data['spacing-curve-data'].map(n => {
		return (Math.round(n * 10) / 10).toFixed(1);
	});

	var chart_stratification = new Chart(ctx_stratification, {
		type: 'line',
		data: {
			labels: spacing_curve_data,
			datasets: [{
				label: 'pho x a',
				data: resistivity_curve_data,
				backgroundColor: 'rgb(255, 0, 0)',
				borderColor: 'rgb(255, 0, 0)',
				fill: false
			}]
		},
		options: {
			events: [],
			elements: {
				point: {
					radius: 0
				}
			},
			scales: {
				yAxes: [{
					ticks: {
						stepSize: 25
					}
				}]
			}
		}
	});

}

// current-phase-ground: 3000
// current-grid: 1200
// defect-duration: 0.6
// grid-width: 50
// grid-length: 40
// gravel-resistivity: 3000
// gravel-height: 0.2
// ea: 3
// eb: 3
// grid-height: 0.6
// rod-height: 3
//-----------------------------------------
//	Caso 1
//
//Espaçamento (m): 1
//Resistências (ohm): 82.7
//Espaçamento (m): 2
//Resistências (ohm): 44.2
//Espaçamento (m): 4
//Resistências (ohm): 16.1
//Espaçamento (m): 6
//Resistências (ohm): 7.7
//Espaçamento (m): 8
//Resistências (ohm): 4.69
//Espaçamento (m): 16
//Resistências (ohm): 1.88
//Espaçamento (m): 32
//Resistências (ohm): 0.905
// -----------------------------------------
//	Caso 2
// Espaçamento (m): 1
// Resistências (ohm): 1814, 1690, 333, 396, 491, 497
// Espaçamento (m): 2
//Resistências (ohm): 549, 622, 190.3, 149.1, 359, 261.8
//Espaçamento (m): 4
//Resistências (ohm): 141.2, 122, 88.3, 80.3, 149.9, 108
//Espaçamento (m): 8
//Resistências (ohm): 40.3, 40, 39, 15.2, 46.2, 28.2
//Espaçamento (m): 14
//Resistências (ohm): 14.6, 14, 13, 15, 16.1, 14.7
//Espaçamento (m): 16
//Resistências (ohm): 10, 12.6, 13, 10.1, 10.2, 9.8
//-----------------------------------------
//	Caso 3
//
//Espaçamento (m): 1
//Resistências (ohm): 20, 18.5, 15
//Espaçamento (m): 2
//Resistências (ohm): 7, 10, 6
//Espaçamento (m): 4
//Resistências (ohm): 2, 3, 1.6
//Espaçamento (m): 8
//Resistências (ohm): 1, 0.4, 1.1
//-----------------------------------------
