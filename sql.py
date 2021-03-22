GET_ALL_USERS = '''SELECT
	user_id, 
	first_name, 
	last_name, 
	user_email, 
	city, 
	state,
	zip,
	phone_number
FROM Application_User
'''

GET_ALL_TUTORS = '''SELECT
	lister_id,
    user_id, 
	Years_experience,
	price_per_hour
FROM Lister
'''

GET_ALL_CLIENTS = '''SELECT
	client_id,
    user_id, 
	date_of_birth
FROM Lister
'''

GET_DETAILED_LISTER_INFO = '''SELECT 
	c.activity_type,
	c.activity_name,
	u.first_name, 
	u.last_name, 
	u.phone_number, 
	l.years_experience, 
	l.price_per_hour, 
	l.lister_id 
FROM application_user u, lister l, teaches t, category c
WHERE u.user_id = l.user_id AND l.lister_id = t.lister_id AND t.category_id = c.category_id
ORDER BY c.activity_type, c.activity_name;
'''


GET_AVG_PRICE_PER_ACTIVITY = '''SELECT c.activity_name, ROUND(AVG(l.price_per_hour),2) AS Average
	FROM lister l
	INNER JOIN teaches t ON l.lister_id = t.lister_id
	INNER JOIN category c ON t.category_id = c.category_id
	GROUP BY c.activity_name
	ORDER BY AVG(l.price_per_hour) DESC;
'''

GET_TUTORS_WITH_RATING = '''SELECT
	au.first_name, au.last_name, r.comment, r.rating
FROM review r
INNER JOIN reviews rs on rs.review_id = r.review_id
INNER JOIN lister l on l.lister_id = rs.lister_id
INNER JOIN application_user au on au.user_id = l.user_id
WHERE rating >= ?;
'''
