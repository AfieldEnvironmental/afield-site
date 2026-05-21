exports.handler = async function (event) {
  var table = (event.queryStringParameters || {}).table;
  if (!table) {
    return { statusCode: 400, body: JSON.stringify({ error: 'missing table param' }) };
  }

  var url =
    'https://api.airtable.com/v0/' +
    process.env.AIRTABLE_BASE +
    '/' +
    encodeURIComponent(table) +
    '?sort[0][field]=Order&sort[0][direction]=asc';

  var res = await fetch(url, {
    headers: { Authorization: 'Bearer ' + process.env.AIRTABLE_TOKEN }
  });

  var data = await res.json();

  return {
    statusCode: res.status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    },
    body: JSON.stringify(data)
  };
};
