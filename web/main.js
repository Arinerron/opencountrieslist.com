/*
 * i use arch btw
 */


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
        1: 'YES',
        2: 'NO'
    }
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


$(document).ready(function() {
    fetch('/data.json').then(response => response.json()).then(data => {
        console.debug('Received data:', data)

        var last_update = (new Date(data['time'] * 1e3)).toLocaleString()
        document.getElementById('last-update').innerText = last_update

        var countriesTableBody = $('#countries-tbody')
        var abbrevs = {
            'CHINA': 'CN'
        }
        for (var country of data['countries']) {
            const tr = document.createElement('tr')
            const cols = [
                _text_el(abbrevs[country['abbreviation']] || country['abbreviation']),
                _text_el(country['name']),
                _classification_el(country),
                _test_required_el(country),
                _url_el(country['url'])
            ]

            for (var col of cols) { tr.append(col) }
            countriesTableBody.append(tr)
        }

        $('#countries').DataTable({
            order: [[ 2, 'desc' ], [ 3, 'desc' ], [ 4, 'asc' ]],
            stateSave: true,
            paging: false,
            columnDefs: [{
                targets: 0,
                className: 'text-center',
                width: '5%'
            }, {
                targets: 1,
                width: '25%'
            }, {
                targets: 2,
                width: '18%'
            }, {
                targets: 3,
                width: '12%'
            }]
        })
    }).catch((error) => {
        console.error('Error:', error)
        alert(`Failed to fetch data: ${error}`)
    })
})

