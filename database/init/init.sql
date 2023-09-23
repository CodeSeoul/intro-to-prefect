create table inventory_history (
    fetch_timestamp timestamp primary key,
    sold int not null default 0,
    pending int not null default 0,
    available int not null default 0,
    unavailable int not null default 0
);
