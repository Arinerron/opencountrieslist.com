/*
 * i use arch btw
 */

const isMobile = /mobi/i.test(navigator.userAgent);


var ready_start_time = (+ new Date())

function _text_el(data) {
    const td = document.createElement('td')
    td.innerText = data
    return td
}


function _url_el(data) {
    const td = document.createElement('td')
    const a = document.createElement('a')
    a.rel = 'noopener noreferer'
    a.href = data
    a.innerText = data
    td.append(a)
    return td
}


function _last_changed_el(country) {
    const td = document.createElement('td')
    var last_changed = country['last_changed'] || 0
    if (country['classification'] === 0) {
        last_changed = 0
    }

    td.innerText = (last_changed ? (new Date(country['last_changed'] * 1e3)).toLocaleDateString() : '')
    td.setAttribute('data-order', ''+last_changed)
    return td
}


function _country_name_el(country) {
    const td = document.createElement('td')
    if (!isMobile) {
        const a = document.createElement('a')
        a.rel = 'noopener noreferer'
        a.href = country['url']
        a.innerText = country['name']
        td.append(a)
    } else {
        td.innerText = country['name']
    }
    return td
}


function _classification_el(country) {
    const classification = country['classification']
    const preformatted = country['preformatted']
    var classNames = {
        0: 'status-unknown',
        1: 'status-moreinfo',
        2: 'status-no',
        3: 'status-rarely',
        4: 'status-sometimes',
        5: 'status-yes'
    }

    var texts = {
        0: 'UNKNOWN',
        1: 'SEE URL',
        2: 'NOT OPEN',
        3: 'VERY HARD TO ENTER',
        4: 'HARD TO ENTER',
        5: 'OPEN'
    }

    const td = document.createElement('td')
    td.className = classNames[classification]
    td.setAttribute('data-order', ''+classification)

    /*
    const button = document.createElement('button')
    const glyph = document.createElement('span')
    glyph.className = 'glyphicon glyphicon-info-sign'
    glyph.setAttribute('aria-hidden', 'true')
    button.onclick = () => {
        alert(preformatted);
        //$('#modal').modal('show');
    }
    td.append(button)*/

    const span = document.createElement('span')
    span.innerText = texts[classification]
    td.append(span)
    if (country['preformatted']) {
        var msg = '<b>Are U.S. citizens permitted to enter the country?</b><br>' + country['preformatted'].join('<br>')
        td.setAttribute('data-toggle', 'tooltip')
        td.setAttribute('data-placement', 'right')
        td.setAttribute('data-html', 'true')
        td.setAttribute('title', msg)
    }
    return td
}


function _test_required_el(country) {
    var test_required = country['test_required']

    // set to N/A if they don't allow entry (covid tests are meaningless)
    if (country['classification'] === 2) {
        test_required = -1
    }

    var classNames = {
        0: 'status-unknown',
        1: 'status-no', // test_required == yes, but we want color
        2: 'status-yes' // test_required == no
    }

    var texts = {
        0: 'UNKNOWN',
        1: 'REQUIRED',
        2: 'NOT REQUIRED'
    }

    classNames[-1] = 'status-no'
    texts[-1] = ''

    const td = document.createElement('td')
    if (classNames[test_required]) {
        td.className = classNames[test_required]
    }
    td.setAttribute('data-order', ''+test_required)
    const span = document.createElement('span')
    span.innerText = texts[test_required]
    td.append(span)
    return td
}


function _quarantine_required_el(country) {
    var quarantine_required = country['quarantine_required']

    // set to N/A if they don't allow entry (covid tests are meaningless)
    if (country['classification'] === 2) {
        quarantine_required = -1
    }

    var classNames = {
        0: 'status-unknown',
        1: 'status-no', // quarantine_required == yes, but we want color
        2: 'status-yes' // quarantine_required == no
    }

    var texts = {
        0: 'UNKNOWN',
        1: 'REQUIRED',
        2: 'NOT REQUIRED'
    }

    classNames[-1] = 'status-no'
    texts[-1] = ''

    const td = document.createElement('td')
    if (classNames[quarantine_required]) {
        td.className = classNames[quarantine_required]
    }
    td.setAttribute('data-order', ''+quarantine_required)
    const span = document.createElement('span')
    span.innerText = texts[quarantine_required]
    td.append(span)
    return td
}


function createMap(data) {
    var start_time = (+ new Date())
    var texts = {
        0: 'Unknown status',
        1: 'See URL for more info',
        2: 'Not open to travelers',
        3: 'Very hard to enter',
        4: 'Hard to enter',
        5: 'Open to travelers'
    }

    var cat_agg = [['Country', 'Classification', {role: 'tooltip', p:{html:true}}]]
    var rows = []
    for (var country of data['countries']) {
        if (country['classification'] == 0) continue;
        cat_agg.push([
            country['abbreviation'], country['classification'], '<p style="white-space: nowrap"><b>' + country['name'] + ':</b> ' + texts[country['classification']] + '</span>'
        ])
        // keep same index
        rows.push(country)
    }

    google.charts.load('current', {
        'packages':['geochart'],
        'mapsApiKey': 'AIzaSyAKam0tf14-8M08QfWSWIZmM8W9gHFyT_o'
    })
    google.charts.setOnLoadCallback(drawRegionsMap)

    function drawRegionsMap() {
        var data = google.visualization.arrayToDataTable(cat_agg)

        var options = {
            colorAxis: {minValue: 0, maxValue: 5, colors: ['#9EA7AD', '#2DCCFF', '#FF3838', '#FF3838', '#FCE83A', '#56F000']},
            backgroundColor: '#f5f5f5',
            datalessRegionColor: '#9EA7AD',
            defaultColor: '#9EA7AD',
            displayMode: 'regions',
            tooltip: {
                isHtml: true
            },
            legend: 'none',
            keepAspectRatio: true
        }

        var chart = new google.visualization.GeoChart(document.getElementById('map-container'))
        google.visualization.events.addListener(chart, 'select', function() {
            var s = chart.getSelection();
            if (s.length) {
                if (!isMobile) {
                    var country = rows[s[0]['row']]
                    console.log('Clicked country', country)
                    window.open(country['url'], '_blank')
                }
            }
        });
        chart.draw(data, options)
        var end_time = (+ new Date())
        console.log('Map load time:', (end_time - start_time)/1000)
    }

}


function setTooltip(el_id, msg) {
    var el = document.getElementById(el_id)
    el.setAttribute('data-toggle', 'tooltip')
    el.setAttribute('data-placement', 'top')
    // data-html set from HTML
    el.setAttribute('title', msg)
}


function addTooltips() {
    var msgs = {
        'Open to Travel': {
            'Open': 'The country allows United States citizens to fly in, regardless of purpose (e.g. tourism)',
            'Hard to Enter': 'The country only allows United States citizens to enter for specific purposes (e.g. returning to home, international school, etc)',
            'Very Hard to Enter': 'Only specific people are granted access to the country (e.g. diplomats, corporate leaders)',
            'Closed': 'No entry to the country is permitted by the country\'s government',
            'See URL': 'Certain portions of the country appear to be open while others aren\'t. Check the URL for more info'
        },
        'Quarantine': {
            'Not Required': 'The country will not require you to quarantine on arrival',
            'Required': 'The country has specified that you will be required to quarantine on arrival. Check the URL to see if there are any relevant exceptions (e.g. through a COVID-19 test)'
        },
        'COVID Test': {
            'Not Required': 'The country has not specified any COVID-19 testing requirements',
            'Required': 'The country has specified COVID-19 testing requirements to enter the country. See the URL for more info'
        },
        'Last Changed': 'This column contains the date of the most recent change to the country\'s travel policy'
    }

    if (!isMobile) {
        for (const [key, val] of Object.entries(msgs)) {
            var tooltipId = 'column-' + key.toLowerCase().replaceAll(' ', '-')
            var inner = document.createElement('ul')
            inner.className = 'text-left'
            if ((typeof val) === 'string') {
                setTooltip(tooltipId, val)
            } else {
                for (const [inner_key, inner_val] of Object.entries(val)) {
                    var li = document.createElement('li')
                    var b = document.createElement('b')
                    b.innerText = inner_key + ':'
                    li.append(b)
                    li.append(' ' + inner_val)
                    inner.append(li)
                }
                setTooltip(tooltipId, inner.outerHTML)
            }
        }
    }

    // TODO: auto update the accordion too
}


$(document).ready(function() {
    var ready_end_time = (+ new Date())
    console.log('Document ready time:', (ready_end_time-ready_start_time)/1000)
    fetch('/data.json').then(response => response.json()).then(data => {
        var data_end_time = (+ new Date())
        console.log('Data ready time:', (data_end_time-ready_end_time)/1000)

        setTimeout(createMap.bind(null, data), 0)

        var start_time = (+ new Date())
        var last_update = (new Date(data['time'] * 1e3)).toLocaleString()
        document.getElementById('last-update').innerText = last_update

        var countriesTableBody = document.getElementById('countries-tbody')
        var abbrevs = {
            'CHINA': 'CN'
        }
        for (var country of data['countries']) {
            const tr = document.createElement('tr')
            const cols = [
                _text_el(abbrevs[country['abbreviation']] || country['abbreviation']),
                _country_name_el(country),
                _classification_el(country),
                _quarantine_required_el(country),
                _test_required_el(country),
                _last_changed_el(country)
            ]

            for (var col of cols) { tr.append(col) }
            countriesTableBody.append(tr)
        }
        var end_time = (+ new Date())
        console.log('Data parsing time:', (end_time-start_time)/1000)

        var start_time = (+ new Date())
        $('#countries').DataTable({
            order: [[ 2, 'desc' ], [ 3, 'desc' ], [ 4, 'desc' ], [ 5, 'asc' ]],
            stateSave: true,
            paging: false,
            responsive: true,
            language: {
                search: '',
                searchPlaceholder: 'Search for a country...'
            },
            columnDefs: [{
                targets: 0,
                className: 'text-center',
                width: '5%',
                orderable: false
            }, {
                targets: 1,
                width: '25%'
            }, {
                targets: 2,
                width: '18%'
            }, {
                targets: 3,
                width: '12%'
            }, {
                targets: 4,
                width: '12%'
            }, {
                targets: 5,
                width: '11%'
            }],
            fixedHeader: true
        })
        $('#countries').removeClass('hidden'); // XXX: messes with sizing
        var end_time = (+ new Date())
        console.log('Table render time:', (end_time - start_time)/1000)

        addTooltips();
        $(function () {
            $('[data-toggle="tooltip"]').tooltip()
        })

        setTimeout(function() { document.getElementById('loading').style.display = 'none'; }, 0)

    }).catch((error) => {
        console.error('Error:', error)
        alert(`Failed to fetch data: ${error}`)
    })
})

