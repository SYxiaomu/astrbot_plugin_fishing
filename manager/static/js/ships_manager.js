document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('shipModal');
    const form = document.getElementById('ship-form');
    if (!modal || !form) return;

    // Reset form on modal open for adding
    document.getElementById('addShipBtn').addEventListener('click', function () {
        document.getElementById('shipModalLabel').textContent = '添加船舶';
        form.action = addUrl;
        form.querySelector('input[name="name"]').value = '';
        form.querySelector('input[name="level"]').value = '';
        form.querySelector('textarea[name="description"]').value = '';
        form.querySelector('input[name="cost_coins"]').value = '';
        form.querySelector('input[name="max_ocean_zone_level"]').value = '1';
        form.querySelector('input[name="required_fish"]').value = '';
    });

    // Handle edit buttons
    document.querySelectorAll('.edit-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const item = JSON.parse(this.getAttribute('data-item-json'));
            document.getElementById('shipModalLabel').textContent = '编辑船舶';
            form.action = editUrlBase + item.ship_id;
            form.querySelector('input[name="name"]').value = item.name;
            form.querySelector('input[name="level"]').value = item.level;
            form.querySelector('textarea[name="description"]').value = item.description || '';
            form.querySelector('input[name="cost_coins"]').value = item.cost_coins;
            form.querySelector('input[name="max_ocean_zone_level"]').value = item.max_ocean_zone_level || 1;
            form.querySelector('input[name="required_fish"]').value = item.required_fish || '';
        });
    });
});
