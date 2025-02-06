    SELECT
        cm.id AS commit_id,
        cm.experiment_id AS experiment_id,
        e.title AS experiment_title,
        cm.order_index AS order_index,
        c.type_name,
        c.description,
        c.parameter_data,
        c.snapshot_id,
        u.name AS annotator_name,
        cm.url
    FROM changes c
    JOIN snapshots s ON c.snapshot_id = s.id
    JOIN annotations a ON s.annotation_id = a.id
    JOIN commits cm ON a.commit_id = cm.id
    JOIN experiments e ON cm.experiment_id = e.id
    JOIN users u ON a.owner_id = u.id
    WHERE e.title IN ('test-refactoring-1', 'test-refactoring-2')
    AND c.type_name != 'Non-Refactoring'